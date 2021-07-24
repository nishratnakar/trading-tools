#!/usr/bin/env python
# coding: utf-8

# # Fetch bhavcopy csv file

# * Download NSE bhavcopy CSV file for a given day. 
# * Bhavcopy is available only after 6:00 pm for each trading day
# * The NSE bhavcopy dowload link URL is of format https://archives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MMM}/cm{DD}{MMM}{YYYY}bhav.csv.zip
# * Example bhavcopy for 25th April 2021 is, https://archives.nseindia.com/content/historical/EQUITIES/2021/APR/cm23APR2021bhav.csv.zip
# 
# **Note: downloaded bhavcopy is a zip file, the CSV file needs to be extracted from it**

# In[1]:


from datetime import datetime, timedelta
import os
import requests
import zipfile
from pathlib import Path


# In[17]:


def downloadUnzip(url,filepath, verbose=True):
    '''Download file and unzip the compressed file. If file cannot be 
    found/uncompressed it return False. Else returns True'''
    if not os.path.exists(filepath):
        if verbose: print('Downloading file from URL:',url)
        zFilePath = filepath + '.zip'
        zfile = open(zFilePath,'wb')
        #NSEIndia doesn't let python program to download bhavcopy unless headers are set.
        #Found this solution on stackoverflow as way to access bhavcopy via python by setting headers and session
        hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*,q=0.8,application/signed-exchange;v=b3;q=0.9',
       'Accept-Encoding': 'gzip, deflate, br',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'gzip, deflate, br',
       'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,hi;q=0.6',
       'Connection': 'keep-alive','Host':'www1.nseindia.com',
       'Cache-Control':'max-age=0',
       'Host':'www1.nseindia.com',
       'Referer':'https://www1.nseindia.com/products/content/derivatives/equities/fo.htm',
       }
        cookie_dict={'bm_sv':'E2109FAE3F0EA09C38163BBF24DD9A7E~t53LAJFVQDcB/+q14T3amyom/sJ5dm1gV7z2R0E3DKg6WiKBpLgF0t1Mv32gad4CqvL3DIswsfAKTAHD16vNlona86iCn3267hHmZU/O7DrKPY73XE6C4p5geps7yRwXxoUOlsqqPtbPsWsxE7cyDxr6R+RFqYMoDc9XuhS7e18='}
        session = requests.session()
        for cookie in cookie_dict:
            session.cookies.set(cookie,cookie_dict[cookie])
        
        with session.get(url,headers = hdr) as response:
            for chunks in response.iter_content(chunk_size=1024):
                zfile.write(chunks)
        zfile.close()
        if verbose: print('Downloading Zip File complete')
        if verbose: print('Uncompressing File:',zFilePath)
        try:
            with zipfile.ZipFile(zFilePath,'r') as compressedFile:
                compressedFile.extractall(Path(zFilePath).parent)
        except zipfile.BadZipFile as e:
            print('Uncompression Failure! BadZipFile',e.with_traceback)
            return False
        if verbose: print('File Decompression Success!')
        if verbose: print('Uncompressed File path:',filepath)
        os.remove(zFilePath)
    else:
        if verbose: print('File already exists:',filepath)
    return True


# In[18]:


def fetchBhavcopy(bhavDay, FOLDER_NAME, bhavFilePath, verbose=True):
    '''Fetches bhavcopy from NSE website for given date (bhavDay) and saves the
    uncompressed csv file at path(bhavFilepath) in given Directory(FOLDER_NAME)'''
    year = bhavDay[5:]
    month = bhavDay[2:5]
    if not os.path.exists(FOLDER_NAME):
        if verbose: print('Directory:',FOLDER_NAME,'does not exists')
        os.makedirs(FOLDER_NAME)
        if verbose: print('Directory:',FOLDER_NAME,'created!')
    # else:
    #     print('Directory:',FOLDER_NAME,'exists')
    bhavURL = 'https://archives.nseindia.com/content/historical/EQUITIES/{0}/{1}/cm{2}bhav.csv.zip'.format(year,month,bhavDay)
    # print(bhavURL)
    return downloadUnzip(bhavURL,bhavFilePath, verbose)
    


# In[14]:


def main(offset=0):
    '''For standalone testing'''
    delta = timedelta(days = offset)
    FOLDER_NAME = 'data/scanner/' #The location where files will be downloaded
    bhavDay = (datetime.today() - delta).strftime('%d%b%Y').upper() #Needs to be a valid trading day
    bhavFileName = 'cm'+bhavDay+'bhav.csv'
    bhavFilePath = os.path.join(FOLDER_NAME,bhavFileName)
    bhavFilePath
    status = fetchBhavcopy(bhavDay, FOLDER_NAME, bhavFilePath)
    if status == False:
        print('Fetching of bhavcopy failed for date:',bhavDay)
    else:
        print('Bhavcopy fetched/found for date:',bhavDay)


# In[16]:


if __name__ == '__main__':
    main()

