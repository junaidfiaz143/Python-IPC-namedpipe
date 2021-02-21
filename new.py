import win32api
import win32security
import win32process
import sys
import win32con
import pywintypes

def attempt_to_logon():
	username = "junaid"
	password = "JD143"
	try:
		hUser = win32security.LogonUser(username, ".",
			password, win32security.LOGON32_LOGON_INTERACTIVE, 
			win32security.LOGON32_PROVIDER_DEFAULT)
	except win32security.error:
		print ("unable to logon")
		return None
	return hUser

def run_as_user(hUser):
	startup = win32process.STARTUPINFO()
	startup.dwFlags = win32process.STARTF_USESHOWWINDOW
	startup.wShowWindow = win32con.SW_SHOW
	startup.lpDesktop = 'winsta0\default'
	try:
		result = win32process.CreateProcessAsUser(hUser, 
			None, # appName
			"C:\\Windows\\notepad.exe", # commandLine
			None, # process attrs
			None, # thread attrs
			0, # inherit handles
			0, # create flags
			None, # new environment dict
			None, # current directory
			startup)  # startup info
		print (result)
	except Exception as e:
		print ("Error: " + str(e))

def print_info(hUser):
	print ("print privs")
	print (win32security.GetTokenInformation(hUser, win32security.TokenPrivileges))

def AdjustPriv(priv, enable=1):
	flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
	htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
	id = win32security.LookupPrivilegeValue(None, priv)
	# print(id)
	if enable:
		newPriv = [(id, win32security.SE_PRIVILEGE_ENABLED)]
	else:
		newPriv = [(id, 0)]
	r = win32security.AdjustTokenPrivileges(htoken, 0, newPriv)
	print(r)

	
# AdjustPriv(win32security.SE_TCB_NAME)
AdjustPriv(win32security.SE_ASSIGNPRIMARYTOKEN_NAME)
AdjustPriv(win32security.SE_INCREASE_QUOTA_NAME)
hUser = attempt_to_logon()
# print_info(hUser)
run_as_user(hUser)