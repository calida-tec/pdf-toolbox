Set shell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonw = "C:\Users\20707\AppData\Local\Programs\Python\Python312\pythonw.exe"
target = """" & pythonw & """" & " " & """" & scriptDir & "\pdf_merge_gui.py" & """"
shell.CurrentDirectory = scriptDir
shell.Run target, 0, False
