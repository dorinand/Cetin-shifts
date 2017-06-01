#!/usr/bin/env python3

import http.client, datetime, calendar, collections, os
from bs4 import BeautifulSoup as bs 

HOST = "85.162.8.155"
HTTPHOST = "".join(["http://", HOST])
PORT = 80
URI = "/index.php?"
URI_CH_SESS = "/php/zmen_session.php"
METHOD_POST = "POST"
METHOD_GET = "GET"
BODY_LOG = "XXXXXXXX"
USER_ID = "66297"
MONTH_SHIFT = 3

"""
Google calendar constants. "when" changed in every iteration.
Included in write_to_calendar() function.
""" 
CALENDAR = "CETIN"
TITLE = "CETIN"
# when = "5/27/2017 07:00" - 
WHERE = "Zastavka: Olsanska"
DESCRIPTION = "POPIS"
DURATION = "720"
DI_REMINDER = "540"
NI_REMINDER = "60"
DI_START = "07:00"
NI_START = "19:00"

def main():
	"""
	Main program
	"""
	days, month, year = getDaysMonthYear()
	# body_change_sess = "".join(["cas=", month, "%2F", year])
	root = getData(month, year)
	user = findUser(root)
	shifts = collections.defaultdict(lambda : "")

	for day in range(1, days + 1):
		shifts[day] = getShift(day, user)

	write_to_calendar(month, year, shifts)

def findUser(root):
	"""
	Function filter USER by USER_ID. 
	"""
	soup = bs(root, "lxml") 
	return soup.find(id=USER_ID)

def getDaysMonthYear():
	"""
	Return days in next month, next month and year of next month.
	"""
	month = datetime.date.today().month + MONTH_SHIFT
	if month > 12:
		month = 1
		year += 1
	year = datetime.date.today().year
	days = calendar.monthrange(year, month)
	return days[1], str(month), str(year)

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

def getResponseData(connection, method, uri, headers, body = ""):
	"""
	Send request and receive data. Return response and data.
	"""
	connection.request(method, uri, body, headers=headers)
	response = connection.getresponse()
	data = response.read().decode("utf-8")

	return response, data

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

def write_to_calendar(month, year, shifts):
	"""
	Function create when argument and command for every shift. Then, upload it to g. calendar.
	"""
	for day in shifts:
		if shifts[day] == None: continue
		time = DI_START if shifts[day] == "DI" else NI_START
		reminder = DI_REMINDER if shifts[day] == "DI" else NI_REMINDER
		
		when ="".join([month, "/", str(day), "/", year, " ", time])
		command = "gcalcli --calendar \"{0}\" --title \"{1}\" --when \"{2}\" --where \"{3}\" \
		--description \"{4}\" --duration \"{5}\" --reminder \"{6}\" add".format(CALENDAR, 
		TITLE, when, WHERE, DESCRIPTION, DURATION, reminder)
		os.system(command)

main()
