-- "Share Printers with iPhone": turns AirPrint sharing on and off without Terminal.
set helper to "/Library/Printers/Gutenprint/bin/airprint-share"
set available to paragraphs of (do shell script quoted form of helper & " list")
if available is {} then
	display dialog "No printers to share yet. Set your printer up on this Mac first." buttons {"OK"} default button 1 with title "Share Printers with iPhone"
	return
end if
set current to paragraphs of (do shell script quoted form of helper & " shared")
set picked to choose from list available with title "Share Printers with iPhone" with prompt "Pick the printers your iPhone and iPad can use. Your Mac has to stay on and awake, and anyone on the same Wi-Fi can print to them." default items current OK button name "Save" cancel button name "Cancel" with multiple selections allowed and empty selection allowed
if picked is false then return
set args to ""
repeat with q in picked
	set args to args & " " & quoted form of (q as text)
end repeat
do shell script quoted form of helper & " set" & args
if picked is {} then
	display dialog "Printer sharing is off." buttons {"OK"} default button 1 with title "Share Printers with iPhone"
else
	display dialog "Done. On your iPhone, tap Share, then Print, and pick your printer." buttons {"OK"} default button 1 with title "Share Printers with iPhone"
end if
