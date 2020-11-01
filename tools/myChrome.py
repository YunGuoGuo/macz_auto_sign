#!/usr/bin/env pyhton

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException



class Chrome:
    def __init__(self, arguments):
        self.option = ChromeOptions()
        self.option.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.option.add_experimental_option('useAutomationExtension', False)
        # self.option.add_argument("--incognito")
        for arg in arguments:
            if arguments[arg] == 'true':
                self.option.add_argument(f"--{arg}")
        self.chrome = webdriver.Chrome(options= self.option)
        self.chrome.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: ()=>undefined})'
        })
        self.chromeWait = WebDriverWait(self.chrome, 10)

    def goto(self, url):
        return self.chrome.get(url)

    def wait(self, css_selector):
        self.chromeWait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))

    def getElement(self, css_selector):
        return self.chromeWait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))

    def switchTo(self, css_selector):
        self.chrome.switch_to.frame(css_selector)

    def switchParent(self):
        self.chrome.switch_to.parent_frame()

    def action(self):
        return ActionChains(self.chrome)

    def close(self):
        self.chrome.close()

    def TimeoutException(self):
        return TimeoutException