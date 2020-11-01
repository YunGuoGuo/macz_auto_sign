#!/usr/bin/env pyhton

import json
import time
import requests
import logging
from io import BytesIO
from tools import chaojiying
from tools import myChrome

Config = json.load(open('./config.json', 'r'))
# Retina screen offset
ScreenOffset = Config['ScreenOffset']
SliderBarOffset = Config['SliderBarOffset']

URL = Config['URL']
maczAccountFile = Config['maczAccountFile']
chaojiyingAccountFile = Config['chaojiyingAccountFile']
chromeOptions = Config['chromeOptions']

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s")
def log(level, *msg):
    text = ' '.join(msg)
    if level == "info":
        logging.info(text)
    elif level == "warning":
        logging.warning(text)
    elif level == "error":
        logging.error(text)


def track(num):
    arr = []
    while (num):
        newNum = num / 2
        arr.append(newNum)
        num = num - newNum
        floatNum = num % 1
        arr[0] += floatNum
        num -= floatNum
    return arr


def parseCaptcha(imgUrl):
    captchaResponse = requests.get(imgUrl)
    imgBytes = BytesIO(captchaResponse.content).getvalue()
    maczAccountData = json.load(open(chaojiyingAccountFile, 'r'))
    chaojiyingUsername = maczAccountData['username']
    chaojiyingPassword = maczAccountData['password']
    chaojiyingSoftId = maczAccountData['soft_id']
    cjy = chaojiying.Chaojiying(chaojiyingUsername, chaojiyingPassword, chaojiyingSoftId)
    cjyRes = cjy.PostPic(imgBytes, 9101)
    if cjyRes['err_no'] == 0:
        # return (x, y)
        picName = f"{int(time.time())}.png"
        fullPicName = f"./data/img/{picName}"
        position = tuple(map(int ,cjyRes['pic_str'].split(',')))
        with open('./data/position_history.list', 'a') as f:
            lineData = f"{position[0]} {position[1]} {picName} {imgUrl}\n"
            f.write(lineData)
        with open(fullPicName, 'wb') as f:
            f.write(imgBytes)
        return position
    else:
        print(cjyRes)
        exit(2)


def slideElementToPosition(chrome, css_selecotor, position):
    sliderBar = chrome.getElement(css_selecotor)
    chrome.action().click_and_hold(sliderBar).perform()
    trackList = track(position[0]/ ScreenOffset - SliderBarOffset)
    for offset in trackList:
        chrome.action().move_by_offset(xoffset=offset, yoffset=0).perform()
        time.sleep(0.2)
    chrome.action().release().perform()


def login(chrome, phone, password):
    # goto index page
    log('info', "goto", URL)
    chrome.goto(URL)
    # click login button
    log('info', "waiting for render...")
    time.sleep(6)
    log('info', f'login account {phone} by phone & password')
    chrome.getElement('#to-login').click()
    # select login way
    chrome.getElement(".phone-login").click()
    # input phone & password
    chrome.getElement("#login-form input[name='username']").send_keys(phone)
    chrome.getElement("#login-form input[name='password']").send_keys(password)
    # click loginBtn
    chrome.getElement("#login-form button").click()
    time.sleep(2)
    # switch to iframe
    log('info', 'switch to captcha iframe')
    captchaIframe = chrome.getElement("#tcaptcha_iframe")
    time.sleep(1)
    chrome.chrome.switch_to.frame(captchaIframe)

    loginState = False
    tryTimes = 0
    while not loginState:
        tryTimes += 1
        if tryTimes > 5:
            log('warning', 'tried over 5 times, login fail...')
            break
        # get captcha
        log('info', 'get captcha url')
        captchaImgUrl = chrome.getElement("#slideBgWrap img").get_attribute('src')
        # use chaojiying to get catpcha gap position
        log('info', 'parse captcha by \'chaojiying\' platform')
        gapPosition = parseCaptcha(captchaImgUrl)
        # verify captcha
        log('info', 'verify captcha')
        slideElementToPosition(chrome, "#tcaptcha_drag_thumb", gapPosition)
        try:
            chrome.getElement(".logined.active")
        except chrome.TimeoutException():
            log('warning', 'verify fail, retry...')
            continue
        loginState = True
    time.sleep(1)
    return loginState


def sign(chrome):
    log('info', 'waiting to sign...')
    chrome.getElement(".sign.oth-item").click()
    startBtn = chrome.getElement(".lottery")
    restTimes = int(chrome.getElement(".lottery>span>em").text)
    if restTimes >= 1:
        log('login', 'remaining times >= 1, start sign...')
        startBtn.click()
        while chrome.getElement(".res-con").text == "":
            time.sleep(1)
        signRes = chrome.getElement(".res-con").text
        log('info', f'sign result: [{signRes}]')
    else:
        log('warning', 'remaining times < 1, skip sign')
    time.sleep(1)
    chrome.getElement("#lottery .prize-close").click()


def loginOut(chrome):
    log('info', 'waiting for logout')
    time.sleep(1)
    userName = chrome.getElement("#user-name")
    log('info', 'logout.')
    logoutState = False
    tryTimes = 0
    while not logoutState:
        tryTimes += 1
        if tryTimes >= 5:
            log('error', 'logout fail over 5 times')
            break
        try:
            chrome.action().move_to_element(userName).perform()
            chrome.getElement(".login-out").click()
            chrome.wait(".login-go.active")
        except chrome.TimeoutException():
            log('warning', 'logout fail, retry...')
            time.sleep(1)
        logoutState = True
    return logoutState



def main():
    chrome = myChrome.Chrome(chromeOptions)
    for userData in json.load(open(maczAccountFile, 'r')):
        phone = str(userData['phone'])
        password = userData['password']
        state = login(chrome, phone, password)
        if not state:
            log('warn', 'login fail, skip this account...')
        else:
            log('info', 'login success!')
        sign(chrome)
        state  = loginOut(chrome)
        if not state:
            log('warn', 'loginout fail, exit...')
        else:
            log('info', 'loginout success!')
        time.sleep(2)
    log('info', 'all account are signed, close chrome and exit process.')
    chrome.close()

if __name__ == '__main__':
    main()

