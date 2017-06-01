#!/usr/bin/env python3

import calendar, collections, datetime, http.client, os, re, smtplib, subprocess
from bs4 import BeautifulSoup as bs 

# login and password to gmail account
USER = "XXXXX"
PASSWORD = "XXXXX"

# Gmail SMTP server address
G_SMTP_ADD = "smtp.gmail.com"

# Email parametres
from_addr = " ".join(["From:", USER])
to_addr = "To: XXXXXX"
subject = "CETIN - Shifts Changed!"

MONTH_SHIFT = 2

HOST = "85.162.8.155"
HTTPHOST = "".join(["http://", HOST])
PORT = 80
URI = "/index.php?"
URI_CH_SESS = "/php/zmen_session.php"
METHOD_POST = "POST"
METHOD_GET = "GET"
BODY_LOG = "XXXXXXn"
USER_ID = "XXXXXX"
MONTH_SHIFT = 1

def main():
	days, month, year = getDaysMonthYear()
	start = "/".join([month, "1", year])
	end = "/".join([str(int(month) + 1), "1", year])

	google_shifts = getGoogleShifts(start, end, days)
	
	root = getData(month, year)
	user = findUser(root)

	shifts = collections.defaultdict(lambda : "")

	for day in range(1, days + 1):
		shifts[day] = getShift(day, user)



	msg = getMessage(shifts, google_shifts, days)
	sendEmail( month, year, msg)

def findUser(root):
	"""
	Function filter USER by USER_ID. 
	"""
	soup = bs(root, "lxml") 
	return soup.find(id=USER_ID)

def getData(month, year):
	"""
	Return data of the user in HTML.
	"""
	body = "".join(["cas=", month, "%2F", year])

	session_id = ""
	connection = http.client.HTTPConnection(HOST, PORT)

	headers = getHeaderPost(ContentLength=len(BODY_LOG), Referer="/")
	response, data = getResponseData(connection, METHOD_POST, URI, headers, BODY_LOG)

	for key, value in response.getheaders():
		if key == "Set-Cookie":
			for x in value.split():
				if "PHPSESSID" in x:
					session_id = x[0:-1]
			break

	headers = getHeaderPost(Cookie=session_id, ContentLength=len(body), Referer=URI)
	response, data = getResponseData(connection, METHOD_POST, URI_CH_SESS, headers, body)

	headers = getHeaderGet(Cookie=session_id, Referer=URI)
	response, data = getResponseData(connection, METHOD_GET, URI, headers)

	return data

def getDaysMonthYear():
	"""
	Return days in next month, next month and year of next month.
	"""
	month = datetime.date.today().month + MONTH_SHIFT
	year = datetime.date.today().year
	days = calendar.monthrange(year, month)
	if month > 12:
		month = 1
		year += 1
	return days[1], str(month), str(year)

def getGoogleShifts(start, end, days):
	"""
	Return list of shifts from google calendar.
	"""
	command = "gcalcli agenda {0} {1} --military --calendar CETIN".format(start, end).split()
	string = subprocess.run(command, stdout=subprocess.PIPE).stdout.decode("utf-8")

	pattern = re.compile("\x1b\[+[0-8]m|\x1b\[+[0-8];[3-4][0-7]m")
	string = re.sub(pattern, "", string)

	google_shifts_list = []
	for i in string.split("\n"):
		if "CETIN" not in i: continue
		google_shifts_list.append(i)

	google_shifts_dict = {i: None for i in range(1, (days +1))}
	for i in google_shifts_list:
		line = i.split()
		# print(int(line[2].lstrip("0")), type(int(line[2].lstrip("0"))))
		google_shifts_dict[int(line[2].lstrip("0"))] = "DI" if line[3] == "07:00" else "NI"

	return google_shifts_dict

def getHeaderGet(Accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
	AcceptEncoding = "deflate, sdch",
	AcceptLanguage = "cs-CZ,cs;q=0.8,en;q=0.6,sk;q=0.4,und;q=0.2",
	CacheControl = "max-age=0",
	Connection = "keep-alive",
	Cookie = "",
	Host = HOST,
	Referer = "",
	UpgradeInsecureRequests = "1",
	UserAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36" ):

	headers_get = { "Accept": Accept,
					"Accept-Encoding": AcceptEncoding,
					"Accept-Language": AcceptLanguage,
					"Cache-Control": CacheControl,
					"Connection": Connection,
					"Cookie": Cookie,
					"Host": Host,
					"Referer": "".join([HTTPHOST, Referer]),
					"Upgrade-Insecure-Requests": UpgradeInsecureRequests,
					"User-Agent": UserAgent
					}
	return headers_get

def getHeaderPost(Accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
	AcceptEncoding = "deflate",
	AcceptLanguage = "cs-CZ,cs;q=0.8,en;q=0.6,sk;q=0.4,und;q=0.2",
	CacheControl = "max-age=0",
	Connection = "keep-alive",
	ContentLength = "",
	ContentType = "application/x-www-form-urlencoded",
	Cookie = "",
	Host = HOST,
	Origin = HTTPHOST,
	Referer = "",
	UpgradeInsecureRequests = "1",
	UserAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36"):

	header_post = { "Accept": Accept, 
					"Accept-Encoding": AcceptEncoding, 
					"Accept-Language": AcceptLanguage,
					"Cache-Control": CacheControl,
					"Connection": Connection,
					"Content-Length": ContentLength,
					"Content-Type": ContentType,
					"Cookie": Cookie,
					"Host": Host,
					"Origin": Origin,
					"Referer": "".join([HTTPHOST, Referer]),
					"Upgrade-Insecure-Requests": UpgradeInsecureRequests,
					"User-Agent": UserAgent
					}
	return header_post

def getMessage(shifts, google_shifts, days):
	msg = ""
	for day in range(1,days + 1):
		if shifts[day] == google_shifts[day]: continue
		msg = "".join([msg, "DAY: {0:.>5}   CETIN: {1:.>6}   GOOGLE: {2:.>6}\n".format(day, str(shifts[day]), str(google_shifts[day]))])
		# print("DEŇ: {0:.>5}   CETIN: {1:.>6}   GOOGLE: {2:.>6}".format(day, str(shifts[day]), str(google_shifts[day])))
	return msg

def getResponseData(connection, method, uri, headers, body = ""):
	"""
	Send request and receive data. Return response and data.
	"""
	connection.request(method, uri, body, headers=headers)
	response = connection.getresponse()
	data = response.read().decode("utf-8")

	return response, data

def getShift(day, user):
	"""
	Function write down DI or NI according to downloaded data. If there is no shift
	function return None.
	"""
	user_id = "".join([USER_ID, "_", str(day)])
	code = user.find(id=user_id)
	for line in str(code).split("\n"):
		line = line.strip() 
		if not line.startswith("&lt;dt&gt;Zkratka:"):
			continue
		
		if "DI" in line:
			order = line.find("DI")
		elif "NI" in line:
			order = line.find("NI")
		else:
			order = -1
		ret = None if order == -1 else line[order:order+2]
	return ret

def sendEmail( month, year, msg="No text..."):
	"""
	This function build final message (subject + msg).
	Then create connection to SMTP  server and send email.
	"""
	if msg == "" : return
	text = "In {0}/{1} was performed some changes.".format(month, year)
	message = "Subject: {0}\n\n{1}\n\n{2}".format(subject, text,msg)
	# print(message)
	server = smtplib.SMTP(host=G_SMTP_ADD)
	server.starttls()
	server.login(USER, PASSWORD)
	server.sendmail(from_addr, to_addr, message)
	server.quit()

main()


