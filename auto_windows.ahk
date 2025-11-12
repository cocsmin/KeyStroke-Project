IntervalMs := 20          ; milliseconds between keys 
DurationMs := 30000       ; total duration in milliseconds (30000 = 30s)
StartTime := A_TickCount  

FileDelete("C:\\keystroke_project\\KeyStroke-Project\\logs\\auto_log.csv")

FileAppend("time_ms,key`n", "C:\\keystroke_project\\KeyStroke-Project\\logs\\auto_log.csv")

while (A_TickCount - StartTime <= DurationMs) {
    ; send 'a' to the active window
    Send("a")
    ; append timestamp and key
    FileAppend(A_TickCount . ",a`n", "C:\\keystroke_project\\KeyStroke-Project\\logs\\auto_log.csv")
    Sleep(IntervalMs)   ; sleep uses parens in v2
}
MsgBox("Done.")
