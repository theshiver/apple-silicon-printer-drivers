/*
 * CUPS raster -> foo2zjs family stream, replacing Ghostscript + foo2*-wrapper on macOS.
 *
 *   cgpdftoraster -> rastertofoo2<family> -> printer
 *
 * Built once per family and linked with that family's unmodified foo2*.c, whose main() is
 * renamed foo2_main (build/build-foo2.sh). It runs in a forked child rather than an exec'd
 * tool, so nothing depends on what the cupsd sandbox lets a filter launch.
 *
 * The PPD (build/gen-foo2-ppds.py) carries the exact arguments upstream's wrapper passes for
 * each paper size: *foo2Args <PageSize> for color, *foo2GrayArgs <PageSize> for mono.
 *
 * License: GPL-2.0-or-later, same as foo2zjs.
 */
#include <cups/cups.h>
#include <cups/ppd.h>
#include <cups/raster.h>
#include <cups/sidechannel.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#define FIRMWARE_DIR "/Library/Printers/Gutenprint/share/foo2zjs/firmware/"
#define MAX_ARGS 64

int foo2_main(int argc, char **argv);

/* 1 = firmware running, 0 = not yet, -1 = can't tell (no USB backend on the other end). */
static int firmware_running(void)
{
    char id[2048];
    int len = sizeof(id) - 1;
    if (cupsSideChannelDoRequest(CUPS_SC_CMD_GET_DEVICE_ID, id, &len, 5.0) != CUPS_SC_STATUS_OK || len <= 0)
        return -1;
    id[len] = 0;
    return strstr(id, "FWVER:") != NULL;
}

/*
 * These printers lose their firmware at power off. Asking the backend first means no daemon
 * and no root: the first job after power on sends it, like upstream's hotplug script does.
 */
static void load_firmware(const char *name)
{
    char path[1024], buf[65536], reply[8];
    const char *dir = getenv("FOO2_FIRMWARE_DIR");
    int len = sizeof(reply), state = firmware_running();
    size_t n;
    FILE *f;

    if (state != 0) {
        fprintf(stderr, "DEBUG: rastertofoo: firmware state %d, nothing to send\n", state);
        return;
    }
    /* the override is for tests; cupsd starts filters with its own clean environment */
    if (strchr(name, '/') || snprintf(path, sizeof(path), "%s%s", dir ? dir : FIRMWARE_DIR, name) >= (int)sizeof(path))
        return;
    if (!(f = fopen(path, "rb"))) {
        fprintf(stderr, "ERROR: rastertofoo: can't open firmware %s: %s\n", path, strerror(errno));
        exit(1);
    }
    fprintf(stderr, "INFO: Sending firmware to the printer\n");
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0)
        if (fwrite(buf, 1, n, stdout) != n)
            exit(1);
    fclose(f);
    fflush(stdout);
    cupsSideChannelDoRequest(CUPS_SC_CMD_DRAIN_OUTPUT, reply, &len, 60.0);
    for (int i = 0; i < 20; i++) {
        sleep(1);
        if (firmware_running() == 1)
            return;
    }
    fprintf(stderr, "WARNING: rastertofoo: printer didn't report firmware after upload\n");
}

/* The PPD size this raster page was rendered for; cupsPageSizeName is often empty. */
static const char *page_name(ppd_file_t *ppd, const cups_page_header2_t *h)
{
    for (int i = 0; i < ppd->num_sizes; i++) {
        ppd_size_t *s = ppd->sizes + i;
        if (abs((int)(s->width - h->PageSize[0])) <= 2 && abs((int)(s->length - h->PageSize[1])) <= 2)
            return s->name;
    }
    return NULL;
}

static pid_t start_foo2(char *args, int *fd)
{
    char *argv[MAX_ARGS + 2], *tok;
    int argc = 0, p[2];
    pid_t pid;

    argv[argc++] = "foo2";
    for (tok = strtok(args, " "); tok && argc <= MAX_ARGS; tok = strtok(NULL, " "))
        argv[argc++] = tok;
    argv[argc] = NULL;
    if (pipe(p) || (pid = fork()) < 0) {
        fprintf(stderr, "ERROR: rastertofoo: can't start encoder: %s\n", strerror(errno));
        exit(1);
    }
    if (pid == 0) {
        dup2(p[0], 0);
        close(p[0]);
        close(p[1]);
        exit(foo2_main(argc, argv));
    }
    close(p[0]);
    *fd = p[1];
    return pid;
}

/* Value of "-g <W>x<H>" (the page in pixels), which foo2* expects the image to match. */
static void page_pixels(const char *args, unsigned *w, unsigned *h)
{
    const char *g = strstr(args, "-g");
    if (!g || sscanf(g + 2, "%ux%u", w, h) != 2) {
        fprintf(stderr, "ERROR: rastertofoo: no page size in %s\n", args);
        exit(1);
    }
}

static void write_plane(FILE *out, const unsigned char *plane, unsigned w, unsigned h)
{
    fprintf(out, "P4\n%u %u\n", w, h);
    if (fwrite(plane, (w + 7) / 8, h, out) != h) {
        fprintf(stderr, "ERROR: rastertofoo: encoder stopped: %s\n", strerror(errno));
        exit(1);
    }
}

/* OR nbits of src into dst starting at bit x, keeping inside the bpl bytes of dst. */
static void put_bits(unsigned char *dst, size_t bpl, unsigned x, const unsigned char *src, unsigned nbits, int invert)
{
    for (unsigned i = 0; i * 8 < nbits; i++) {
        unsigned char v = invert ? ~src[i] : src[i];
        size_t b = (x + i * 8) / 8;
        unsigned s = (x + i * 8) & 7;

        /* bits past the raster's own width are padding, not ink */
        if (nbits - i * 8 < 8)
            v &= 0xff << (8 - (nbits - i * 8));
        if (b < bpl)
            dst[b] |= v >> s;
        if (s && b + 1 < bpl)
            dst[b + 1] |= v << (8 - s);
    }
}

/*
 * Copy one raster page into P4 planes of exactly w x rows. cgpdftoraster renders only the
 * PPD's imageable area, so the raster goes back where that area sits on the page; anything
 * past the page is cropped and the rest stays white.
 * Mono is one plane (K, or W where 1 is white); color is banded CMYK, four planes.
 */
static int read_page(cups_raster_t *r, const cups_page_header2_t *h, unsigned char **planes, int n, unsigned w, unsigned rows)
{
    size_t bpl = (w + 7) / 8, band = h->cupsBytesPerLine / n;
    unsigned char *line = malloc(h->cupsBytesPerLine);
    int invert = h->cupsColorSpace == CUPS_CSPACE_W || h->cupsColorSpace == CUPS_CSPACE_SW;
    unsigned x0 = (unsigned)(h->cupsImagingBBox[0] * h->HWResolution[0] / 72 + 0.5);
    unsigned y0 = (unsigned)((h->cupsPageSize[1] - h->cupsImagingBBox[3]) * h->HWResolution[1] / 72 + 0.5);

    if (!line)
        return -1;
    for (int p = 0; p < n; p++)
        memset(planes[p], 0, bpl * rows);
    for (unsigned y = 0; y < h->cupsHeight; y++) {
        if (cupsRasterReadPixels(r, line, h->cupsBytesPerLine) != h->cupsBytesPerLine) {
            free(line);
            return -1;
        }
        if (y + y0 >= rows)
            continue;
        for (int p = 0; p < n; p++) {
            unsigned char *dst = planes[p] + (y + y0) * bpl;
            put_bits(dst, bpl, x0, line + p * band, h->cupsWidth, invert);
            if (w & 7)
                dst[bpl - 1] &= 0xff << (8 - (w & 7));
        }
    }
    free(line);
    return 0;
}

int main(int argc, char **argv)
{
    cups_raster_t *raster;
    cups_page_header2_t h;
    ppd_file_t *ppd;
    ppd_attr_t *attr;
    unsigned char *planes[4] = {0};
    unsigned w = 0, rows = 0;
    int fd = 0, status = 0, pages = 0, input = 0;
    pid_t child = 0;
    FILE *out = NULL;

    if (argc < 6 || argc > 7) {
        fprintf(stderr, "Usage: %s job user title copies options [file]\n", argv[0]);
        return 1;
    }
    setbuf(stderr, NULL);
    signal(SIGPIPE, SIG_IGN);
    if (argc == 7 && (input = open(argv[6], O_RDONLY)) < 0) {
        perror("ERROR: rastertofoo: can't open input");
        return 1;
    }
    if (!(ppd = ppdOpenFile(getenv("PPD")))) {
        fprintf(stderr, "ERROR: rastertofoo: can't open the PPD\n");
        return 1;
    }
    raster = cupsRasterOpen(input, CUPS_RASTER_READ);

    while (cupsRasterReadHeader2(raster, &h)) {
        int color = h.cupsColorSpace == CUPS_CSPACE_CMYK;
        int n = color ? 4 : 1;

        if (h.cupsBitsPerColor != 1 || (color && h.cupsColorOrder != CUPS_ORDER_BANDED) || !h.cupsWidth || !h.cupsHeight) {
            fprintf(stderr, "ERROR: rastertofoo: unexpected raster: %u bits, space %d, order %d\n",
                    h.cupsBitsPerColor, h.cupsColorSpace, h.cupsColorOrder);
            return 1;
        }
        if (!child) {
            const char *name = page_name(ppd, &h);
            char args[1024];

            if (!name || !(attr = ppdFindAttr(ppd, color ? "foo2Args" : "foo2GrayArgs", name))) {
                fprintf(stderr, "ERROR: rastertofoo: paper %ux%u is not supported\n", h.PageSize[0], h.PageSize[1]);
                return 1;
            }
            snprintf(args, sizeof(args), "%s", attr->value);
            page_pixels(args, &w, &rows);
            for (int p = 0; p < 4; p++)
                if (!(planes[p] = malloc((size_t)((w + 7) / 8) * rows))) {
                    fprintf(stderr, "ERROR: rastertofoo: out of memory\n");
                    return 1;
                }
            if ((attr = ppdFindAttr(ppd, "foo2Firmware", NULL)))
                load_firmware(attr->value);
            fflush(stdout);
            child = start_foo2(args, &fd);
            out = fdopen(fd, "wb");
        }
        fprintf(stderr, "PAGE: %d %u\n", ++pages, h.NumCopies ? h.NumCopies : 1);
        if (read_page(raster, &h, planes, n, w, rows)) {
            fprintf(stderr, "ERROR: rastertofoo: raster ended early\n");
            return 1;
        }
        for (int p = 0; p < n; p++)
            write_plane(out, planes[p], w, rows);
    }
    if (!child) {
        fprintf(stderr, "ERROR: rastertofoo: no pages\n");
        return 1;
    }
    fclose(out);
    waitpid(child, &status, 0);
    cupsRasterClose(raster);
    ppdClose(ppd);
    if (!WIFEXITED(status) || WEXITSTATUS(status)) {
        fprintf(stderr, "ERROR: rastertofoo: encoder failed (status %d)\n", status);
        return 1;
    }
    return 0;
}
