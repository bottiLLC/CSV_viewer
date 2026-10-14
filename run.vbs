Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)

Args = ""
For Each Arg In WScript.Arguments
    Args = Args & " """ & Arg & """"
Next

WshShell.CurrentDirectory = ScriptDir
WshShell.Run "cmd.exe /c run.bat" & Args, 0, False
