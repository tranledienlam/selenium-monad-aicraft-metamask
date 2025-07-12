
import argparse
from selenium.webdriver.common.by import By

from browser_automation import BrowserManager, Node
from utils import Utility
from w_metamask import Setup as MetamaskSetup, Auto as MetamaskAuto

PROJECT_URL = "https://aicraft.fun/projects/fizen?ref=1OPR79EINL"

class Setup:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile
        self.metamask_setup = MetamaskSetup(node, profile)
        
    def _run(self):
        self.metamask_setup._run()
        self.node.new_tab(f'{PROJECT_URL}', method="get")
        Utility.wait_time(10)

class Auto:
    def __init__(self, node: Node, profile: dict) -> None:
        self.driver = node._driver
        self.node = node
        self.profile_name = profile.get('profile_name')
        self.password = profile.get('password')
        self.metamask_auto = MetamaskAuto(node, profile)
    
    def popup_sign(self):
        h2_els = self.node.find_all(By.TAG_NAME, 'h2')
        for h2 in h2_els:
            if 'AICraft needs to connect to your wallet'.lower() in h2.text.lower():
                self.node.find_and_click(By.XPATH, '//button[contains(text(),"Sign")]')
                self.metamask_auto.confirm('confirm')
    def connect(self):
        btns = self.node.find_all(By.TAG_NAME, 'button')
        for btn in btns:
            if 'connect wallet' in btn.text.lower():
                self.node.click(btn)
                selectors = [
                    (By.CSS_SELECTOR, 'w3m-modal.open'),
                    (By.CSS_SELECTOR, 'w3m-router'),
                    (By.CSS_SELECTOR, 'w3m-connect-view'),
                    (By.CSS_SELECTOR, 'w3m-wallet-login-list'),
                    (By.CSS_SELECTOR, 'w3m-connector-list'),
                    (By.CSS_SELECTOR, 'w3m-connect-injected-widget'),
                    (By.CSS_SELECTOR, '[name="MetaMask"]')
                ]
                metamask_btn = self.node.find_in_shadow(selectors)
                if metamask_btn:
                    self.node.click(metamask_btn)
                    self.metamask_auto.confirm('Connect')
                    self.metamask_auto.confirm('Approve')
                    self.popup_sign()
                    return self.connect()
                
            elif 'Switch to Monad'.lower() in btn.text.lower():
                self.node.click(btn)
                self.metamask_auto.confirm('approve')
                return self.connect()

            elif 'your votes' in btn.text.lower():
                return True
        
        return False

    def get_votes(self):
        btns = self.node.find_all(By.TAG_NAME, 'button')
        for btn in btns:
            if 'your votes' in btn.text.lower():
                text_vote = self.node.get_text(By.XPATH, './..//button[last()]', btn)
                if text_vote:
                    try:
                        votes = int(text_vote)
                        return votes
                    except Exception:
                        self.node.log('Không thể chuyển text vote thành int')

                return
        return
    def confirm_vote(self):
        div_els = self.node.find_all(By.TAG_NAME, 'div')
        for div in div_els:
            if 'Sign request'.lower() in div.text.lower():
                self.metamask_auto.confirm('confirm')
                return
            elif 'Your transaction is on the way'.lower() in div.text.lower():
                self.metamask_auto.confirm('confirm')
                return

    def vote(self):
        p_els = self.node.find_all(By.TAG_NAME, 'p')
        for p in p_els:
            if 'Travel AI Agent from Vietnam'.lower() in p.text.lower():
                p_parent = self.node.find(By.XPATH, './../..', p)
                if p_parent:
                    self.node.find_and_click(By.XPATH, './/button[last()]', p_parent)
                    self.confirm_vote()
                    self.confirm_vote()
                    div_els = self.node.find_all(By.TAG_NAME, 'div')
                    for div in div_els:
                        if '''You’ve voted for your country's AI Agent'''.lower() in div.text.lower():
                            return True
                break
        return False

    def _run(self):
        if not self.metamask_auto._run():
            return
        self.node.new_tab(f'{PROJECT_URL}', method="get")
        # load xong trang
        self.node.find(By.XPATH, '//h2[contains(text(),"ai agent")]')

        self.popup_sign()
        if not self.connect():
            return
        
        done = 0
        while self.get_votes() and self.vote():
            done +=1
        self.node.snapshot(f'Đã hoàn thành {done} votes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help="Chạy ở chế độ tự động")
    parser.add_argument('--headless', action='store_true', help="Chạy trình duyệt ẩn")
    parser.add_argument('--disable-gpu', action='store_true', help="Tắt GPU")
    args = parser.parse_args()

    profiles = Utility.read_data('profile_name', 'password')
    if not profiles:
        print("Không có dữ liệu để chạy")
        exit()

    browser_manager = BrowserManager(AutoHandlerClass=Auto, SetupHandlerClass=Setup)
    browser_manager.config_extension('Meta-Wallet-*.crx')
    browser_manager.run_terminal(
        profiles=profiles,
        max_concurrent_profiles=4,
        block_media=True,
        auto=args.auto,
        headless=args.headless,
        disable_gpu=args.disable_gpu,
    )