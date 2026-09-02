Option Explicit
Dim shell, fso, root, desktop, shortcutPath, pythonw, pythonexe, mainPy, launcher, iconPath, link

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
desktop = shell.SpecialFolders("Desktop")
shortcutPath = desktop & "\Infinity OS V7 REBORN.lnk"
pythonw = root & "\.venv\Scripts\pythonw.exe"
pythonexe = root & "\.venv\Scripts\python.exe"
mainPy = root & "\main.py"
launcher = root & "\RUN-INFINITY.bat"
iconPath = root & "\assets\infinity.ico"

If Not fso.FileExists(mainPy) Then
    WScript.Echo "main.py was not found: " & mainPy
    WScript.Quit 2
End If

Set link = shell.CreateShortcut(shortcutPath)

If fso.FileExists(pythonw) Then
    link.TargetPath = pythonw
    link.Arguments = Chr(34) & mainPy & Chr(34)
ElseIf fso.FileExists(pythonexe) Then
    link.TargetPath = pythonexe
    link.Arguments = Chr(34) & mainPy & Chr(34)
Else
    link.TargetPath = launcher
    link.Arguments = ""
End If

link.WorkingDirectory = root
link.Description = "Infinity OS V7 REBORN — Ultimate"
If fso.FileExists(iconPath) Then
    link.IconLocation = iconPath & ",0"
End If
link.Save

If Not fso.FileExists(shortcutPath) Then
    WScript.Echo "Windows did not create the shortcut."
    WScript.Quit 3
End If

WScript.Echo "Desktop shortcut created: " & shortcutPath
WScript.Quit 0
