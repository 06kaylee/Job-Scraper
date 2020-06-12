import requests
from bs4 import BeautifulSoup
import pandas as pd 
import time
import argparse
import sys
import smtplib, ssl, email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
import schedule

parser = argparse.ArgumentParser(description="Find jobs at a specified location")
parser.add_argument("Job", help="Enter the job you are looking for. Example: Nursing")
parser.add_argument("City", help = "Enter the city. Example: Seattle")
parser.add_argument("StateAbbrev", help = "Enter the state abbreviation. Example: WA")
parser.add_argument("Email", help = "Enter your gmail address. Example: test123@gmail.com")
args = parser.parse_args()

job = args.Job
city = args.City
state = args.StateAbbrev
sender_email = args.Email
receiver_email = args.Email


def job_title(soup):
    jobs = []
    for section in soup.find_all(name="section", attrs = {"class": "card-content"}):
        for h2 in section.find_all(name = "h2", attrs = {"class": "title"}):
            jobs.append(h2.a.text.strip())
    return jobs

def job_link(soup):
    links = []
    for section in soup.find_all(name = "section", attrs = {"class": "card-content"}):
        for h2 in section.find_all(name = "h2", attrs = {"class": "title"}):
            links.append(h2.a.get("href"))
    return links

def job_company(soup):
    companies = []
    for section in soup.find_all(name="section", attrs = {"class": "card-content"}):
        for div in section.find_all(name = "div", attrs = {"class": "company"}):
            for span in div.find_all(name = "span", attrs = {"class": "name"}):
                companies.append(span.text.strip())
    return companies


def job_location(soup):
    locations = []
    for section in soup.find_all(name="section", attrs = {"class": "card-content"}):
        for div in section.find_all(name ="div", attrs = {"class": "location"}):
            for span in div.find_all(name = "span", attrs = {"class": "name"}):
                locations.append(span.text.strip())
    return locations

def set_up():
    url = f'https://www.monster.com/jobs/search/?q={job}&where={city}__2C-{state}'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup


def get_info(soup):
    columns = ["Job Title", "Company", "Location", "Link"]
    titles = job_title(soup)
    companies = job_company(soup)
    locations = job_location(soup)
    links = job_link(soup)
    df = pd.DataFrame(list(zip(titles, companies, locations, links)), columns = columns)
    return df

def main():
    soup = set_up()
    df = get_info(soup)
    df.to_csv('results.csv', index = False)
    send_mail()

def send_mail():
    port = 465
    
    #base message
    subject = "Jobs"
    body = "Jobs found today: "

    
    #create a multipart message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = sender_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    filename = 'results.csv'
    
    #open csv in binary mode
    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    
    #encode file in ascii chars to send by email
    encoders.encode_base64(part)

    #add header to attachment
    part.add_header("Content-Disposition", f"attachment; filename = {filename}")

    #add attachment to message
    message.attach(part)
    text = message.as_string()

    #secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context = context) as server:
        while True:
            password = getpass.getpass()
            try:
                server.login(sender_email, password)
            except smtplib.SMTPAuthenticationError:
                print("If your gmail account is set up with 2-step verification, please enter your app password instead: ")
                continue
            else:
               server.sendmail(sender_email, receiver_email, text)
               print("Email has been sent")
               break 

        
# schedule.every(1).minutes.do(main)
main()