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


def downloadUnzip(url,filepath):
    '''Download file and unzip the compressed file. If file cannot be 
    found/uncompressed it return False. Else returns True'''
    if not os.path.exists(filepath):
        print('Downloading file from URL:',url)
        zFilePath = filepath + '.zip'
        zfile = open(zFilePath,'wb')
        with requests.get(url,verify=False, stream=True) as response:
            for chunks in response.iter_content(chunk_size=1024):
                zfile.write(chunks)
        zfile.close()
        print('Downloading Zip File complete')
        print('Uncompressing File:',zFilePath)
        try:
            with zipfile.ZipFile(zFilePath,'r') as compressedFile:
                compressedFile.extractall(Path(zFilePath).parent)
        except zipfile.BadZipFile as e:
            print('Uncompression Failure! BadZipFile',e.with_traceback)
            return False
        print('File Decompression Success!')
        print('Uncompressed File path:',filepath)
        os.remove(zFilePath)
    # else:
    #     print('File already exists:',filepath)
    return True


# In[18]:


def fetchBhavcopy(bhavDay, FOLDER_NAME, bhavFilePath):
    '''Fetches bhavcopy from NSE website for given date (bhavDay) and saves the
    uncompressed csv file at path(bhavFilepath) in given Directory(FOLDER_NAME)'''
    year = bhavDay[5:]
    month = bhavDay[2:5]
    if not os.path.exists(FOLDER_NAME):
        print('Directory:',FOLDER_NAME,'does not exists')
        os.makedirs(FOLDER_NAME)
        print('Directory:',FOLDER_NAME,'created!')
    # else:
    #     print('Directory:',FOLDER_NAME,'exists')
    bhavURL = 'https://archives.nseindia.com/content/historical/EQUITIES/{0}/{1}/cm{2}bhav.csv.zip'.format(year,month,bhavDay)
    # print(bhavURL)
    return downloadUnzip(bhavURL,bhavFilePath)
    


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

