/*
 * On-demand USB hotplug firmware loader for host-based HP LaserJet printers (foo2zjs family).
 *
 * Launched by launchd via LaunchEvents (com.apple.iokit.matching) when a supported printer is
 * plugged in or powered on. Uploads the matching sihp*.dl firmware in its own CUPS usb backend
 * invocation so the printer can reset/re-enumerate cleanly before any print job starts.
 *
 * License: GPL-2.0-or-later, same as foo2zjs.
 */
#include <ctype.h>
#include <dispatch/dispatch.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
#include <xpc/xpc.h>

#define DEFAULT_USB_BACKEND "/usr/libexec/cups/backend/usb"
#define DEFAULT_FIRMWARE_DIR "/Library/Printers/Gutenprint/share/foo2zjs/firmware/"

struct fw_entry {
    const char *model;
    const char *file;
};

static const struct fw_entry FW_MODELS[] = {
    {"HP LaserJet 1000",   "sihp1000.dl"},
    {"HP LaserJet 1005",   "sihp1005.dl"},
    {"HP LaserJet 1018",   "sihp1018.dl"},
    {"HP LaserJet 1020",   "sihp1020.dl"},
    {"HP LaserJet P1005",  "sihpP1005.dl"},
    {"HP LaserJet P1006",  "sihpP1006.dl"},
    {"HP LaserJet P1007",  "sihpP1005.dl"},
    {"HP LaserJet P1008",  "sihpP1006.dl"},
    {"HP LaserJet P1505n", "sihpP1505.dl"},
    {"HP LaserJet P1505",  "sihpP1505.dl"},
    {NULL, NULL}
};

static const char *usb_backend_path(void)
{
    if (geteuid() != 0) {
        const char *env = getenv("FOO2_USB_BACKEND");
        if (env && *env)
            return env;
    }
    return DEFAULT_USB_BACKEND;
}

static const char *firmware_dir_path(void)
{
    if (geteuid() != 0) {
        const char *env = getenv("FOO2_FIRMWARE_DIR");
        if (env && *env)
            return env;
    }
    return DEFAULT_FIRMWARE_DIR;
}

static const char *match_firmware(const char *line)
{
    const char *mdl = strstr(line, "MDL:");
    const char *end;
    size_t len;

    if (!mdl || strstr(line, "FWVER:"))
        return NULL;
    mdl += 4;
    end = strpbrk(mdl, ";\"\r\n");
    len = end ? (size_t)(end - mdl) : strlen(mdl);
    while (len > 0 && isspace((unsigned char)mdl[len - 1]))
        len--;

    for (const struct fw_entry *e = FW_MODELS; e->model; e++) {
        if (strlen(e->model) == len && strncasecmp(mdl, e->model, len) == 0)
            return e->file;
    }
    return NULL;
}

static int upload_firmware(const char *backend, const char *uri, const char *fw_path)
{
    pid_t pid;
    int status = 0;

    if (access(fw_path, R_OK) != 0)
        return -1;

    pid = fork();
    if (pid < 0)
        return -1;
    if (pid == 0) {
        char *argv[] = {(char *)backend, "1", "root", "firmware", "1", "", (char *)fw_path, NULL};
        setenv("DEVICE_URI", uri, 1);
        execv(backend, argv);
        _exit(127);
    }
    while (waitpid(pid, &status, 0) < 0 && errno == EINTR)
        ;
    return (WIFEXITED(status) && WEXITSTATUS(status) == 0) ? 0 : -1;
}

static int scan_and_load(void)
{
    const char *backend = usb_backend_path();
    const char *fw_dir = firmware_dir_path();
    int p[2], loaded = 0, status = 0;
    pid_t pid;
    FILE *fp;
    char line[4096];

    if (pipe(p) != 0)
        return -1;
    pid = fork();
    if (pid < 0) {
        close(p[0]);
        close(p[1]);
        return -1;
    }
    if (pid == 0) {
        char *argv[] = {(char *)backend, NULL};
        dup2(p[1], STDOUT_FILENO);
        close(p[0]);
        close(p[1]);
        execv(backend, argv);
        _exit(127);
    }
    close(p[1]);

    fp = fdopen(p[0], "r");
    if (!fp) {
        close(p[0]);
        waitpid(pid, &status, 0);
        return -1;
    }

    while (fgets(line, sizeof(line), fp)) {
        const char *fw = match_firmware(line);
        char *uri_start, *uri_end, uri[1024], fw_path[1024];
        size_t uri_len;

        if (!fw)
            continue;
        uri_start = strstr(line, "usb://");
        if (!uri_start)
            continue;
        uri_end = strpbrk(uri_start, " \t\r\n");
        uri_len = uri_end ? (size_t)(uri_end - uri_start) : strlen(uri_start);
        if (uri_len == 0 || uri_len >= sizeof(uri))
            continue;
        memcpy(uri, uri_start, uri_len);
        uri[uri_len] = '\0';

        if (snprintf(fw_path, sizeof(fw_path), "%s%s", fw_dir, fw) >= (int)sizeof(fw_path))
            continue;
        if (upload_firmware(backend, uri, fw_path) == 0) {
            fprintf(stderr, "foo2-firmware-loader: uploaded %s to %s\n", fw, uri);
            loaded++;
        } else {
            fprintf(stderr, "foo2-firmware-loader: failed to upload %s to %s\n", fw, uri);
        }
    }
    fclose(fp);
    while (waitpid(pid, &status, 0) < 0 && errno == EINTR)
        ;
    return loaded;
}

static dispatch_source_t idle_timer = NULL;

static void arm_exit(dispatch_queue_t q)
{
    if (idle_timer) {
        dispatch_source_cancel(idle_timer);
        dispatch_release(idle_timer);
        idle_timer = NULL;
    }
    idle_timer = dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER, 0, 0, q);
    dispatch_source_set_timer(idle_timer, dispatch_time(DISPATCH_TIME_NOW, 8 * NSEC_PER_SEC), DISPATCH_TIME_FOREVER, NSEC_PER_SEC);
    dispatch_source_set_event_handler(idle_timer, ^{
        exit(0);
    });
    dispatch_resume(idle_timer);
}

int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "--once") == 0)
        return scan_and_load() < 0 ? 1 : 0;

    dispatch_queue_t q = dispatch_queue_create("com.github.apple-silicon-printer-drivers.foo2-firmware", DISPATCH_QUEUE_SERIAL);

    xpc_set_event_stream_handler("com.apple.iokit.matching", q, ^(xpc_object_t event) {
        (void)event;
        if (idle_timer) {
            dispatch_source_cancel(idle_timer);
            dispatch_release(idle_timer);
            idle_timer = NULL;
        }
        sleep(2);
        scan_and_load();
        arm_exit(q);
    });

    dispatch_async(q, ^{ arm_exit(q); });
    dispatch_main();
    return 0;
}
