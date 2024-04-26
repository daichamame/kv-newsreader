from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.clock import Clock
import sys
import datetime
import feedparser
import webbrowser

#--------------------------------------------------------------------------------------------------
# 終了コマンド
#--------------------------------------------------------------------------------------------------
class PopupExitDialog(Popup):
    pass
    # プログラム終了
    def exec_exit(self):
       sys.exit()
#--------------------------------------------------------------------------------------------------
# メインウィジット
#--------------------------------------------------------------------------------------------------
class TileWidget(Widget):
    weekday = ["月","火","水","木","金","土","日"]
    cat_cnt = 0             # 表示しているニュースのカテゴリ番号
    cat_name = ''           # 表示しているニュースのカテゴリ名
    cat_interval = 1200     # 表示しているニュースのカテゴリを自動で切り替える時間（秒）
    news_list = {}          # 取得したニュース格納用
    news_cnt = 0            # 表示しているニュースの番号
    news_interval = 30      # 1つのニュースを表示する時間（秒）
    dispnews_event = ''      # ニュース表示自動切換えイベント
    getnews_event = ''      # ニュースカテゴリ自動切換えイベント
    max_url = 0
    rssfeedurl ={
        0:['ボタン0','rssの取得URL'],
        1:['ボタン1','rssの取得URL'],
        2:['ボタン2','rssの取得URL'],
        3:['ボタン3','rssの取得URL'],
        4:['ボタン4','rssの取得URL'],
        5:['ボタン5','rssの取得URL'],
        6:['ボタン6','rssの取得URL'],
        7:['ボタン7','rssの取得URL'],
    }
    # 初期処理
    def __init__(self, **kwargs):
        Window.size=(640,480)                               # ウィンドウサイズの指定
        super(TileWidget, self).__init__(**kwargs)
        Clock.schedule_once(self.init_callback,1)           # 起動時の初期化処理
        Clock.schedule_interval(self.clock_callback, 1)     #　1秒ごとにclock_callbackを実行するように設定
        self.dispnews_event=Clock.schedule_interval(self.display_news_callback,self.news_interval) 


    # 起動時の初期化処理
    def init_callback(self,dt):
        self.max_url = len(self.rssfeedurl)
        for i in range(self.max_url):
            btnid = 'btn_' + str(i)
            self.ids[btnid].text=self.rssfeedurl[i][0]
        self.get_news(0)                                    # 初期表示用に主要ニュース取得        
        self.display_news(0)                                # ニュースを表示
        self.ids.autoplay.active = True

    # 時計表示
    def clock_callback(self,dt):
        # 日時取得
        now_date = datetime.datetime.now()                  # 現在の取得
        self.ids.lbl_date.text=now_date.strftime('%Y年%m月%d日') + " (" + self.weekday[now_date.weekday()] + ") " + now_date.strftime('%H:%M')      # 日付

    # 次のニュース表示（時間実行）
    def display_news_callback(self,dt):
        self.display_news('up')

    # 次のニュースカテゴリを取得（時間実行）
    def get_news_callback(self,dt):
        self.get_news('up')
        self.display_news(0)                                # ニュースを表示

    # メニューボタン押下時の処理
    def menu_sw(self,cmd):
        try:
            int(cmd)
        except:
            if cmd == 'prev_news':                          # 前のニュースへ
                self.display_news('down')
            elif cmd == 'next_news':                        # 次のニュースへ
                self.display_news('up')
        else:
            self.get_news(cmd)
            self.display_news(0)
    
    # ブラウザでリンクを開く
    def open_link(self):
        if(len(self.news_list.entries) != 0):
            if(self.news_list.entries[self.news_cnt].link != ""):
                webbrowser.open(self.news_list.entries[self.news_cnt].link)

    # 自動再生と手動再生の切り替え
    def switch_modes(self,status):
        print(status)
        # ニュースの取得スケジュールをキャンセル
        try:
            self.getnews_event.cancel()
        except:
            print("failed to cancel getnews_event")            
        # ニュースの表示スケジュールのキャンセル
        try:
            self.dispnews_event.cancel()
        except:
            print("failed to cancel dispnews_event")
        if(status):
            # ニュースの取得スケジュールを再定
            try:
                self.getnews_event=Clock.schedule_interval(self.get_news_callback,self.cat_interval)
            except:
                print("failed to start getnews_event")            
            # ニュースの表示スケジュールを設定
            try:
                self.dispnews_event=Clock.schedule_interval(self.display_news_callback,self.news_interval)
            except:
                print("failed to start dispnews_event")

    # ニュース取得
    def get_news(self,no):
        try:
            int(no)
        except:                                             
            # 取得するニュースカテゴリの計算
            self.cat_cnt = (no=='up')*(self.cat_cnt < self.max_url-1)*(self.cat_cnt+1) + (no=='down')*(self.cat_cnt > 0)*(self.cat_cnt-1)+(no=='down')*(self.cat_cnt == 0)*(self.max_url -1 )
        else:
            self.cat_cnt = int(no)*(int(no)<self.max_url)

        self.news_list = feedparser.parse(self.rssfeedurl[self.cat_cnt][1])      # ニュースを取得
        self.news_cnt = 0                                   # 表示ニュース番号を0に設定   
        try:
            self.cat_name = self.news_list.feed.title       # ニュースカテゴリ名取得
        except:
            self.cat_name = "-"
        if(self.ids.autoplay.active):
            # ニュースの取得でのスケジュールを一度キャンセルし再設定
            try:
                self.getnews_event.cancel()
            except:
                print("failed to cancel getnews_event")            
            else:
                # ニュースの取得間隔を設定
                self.getnews_event=Clock.schedule_interval(self.get_news_callback,self.cat_interval)

    # ニュースを表示
    def display_news(self,ct):
        max_item = len(self.news_list.entries)
        # ニュースの件数が0件
        if(max_item == 0):
            self.ids.lbl_title.text = ""
            self.ids.newstitle.text = ""
            self.ids.newscontent.text = "表示するニュースがありません。取得URLを確認してください"
            self.ids.newslink.text = ""
            self.ids.newslink.text = ""
            return

        # 表示するニュースの番号を設定
        try:
            int(ct)
        except:                                            
            # ctが数字でなければ、表示するニュース番号の計算
            self.news_cnt = (ct=='up')*(self.news_cnt < max_item-2)*(self.news_cnt+1) + (ct=='down')*(self.news_cnt > 0)*(self.news_cnt-1)+(ct=='down')*(self.news_cnt == 0)*(max_item -1 )
        else:
            # 数字ならば、番号を代入
            self.news_cnt = int(ct) * (int(ct)<max_item)

        # 配信日付の取得
        try:
            update_date =  self.news_list.entries[self.news_cnt].published
        except:
            # publishedがない場合、updatedの値を使用
            update_date =  self.news_list.entries[self.news_cnt].updated
        
        self.ids.lbl_title.text = self.cat_name # カテゴリ名の表示

        self.ids.newstitle.text = self.news_list.entries[self.news_cnt].title + "(" + str(self.news_cnt + 1) + "/" + str(max_item) + ")"
        # 記事内容の表示
        try:
            self.ids.newscontent.text = self.news_list.entries[self.news_cnt].description + "(" + update_date  + ")"
        except:
            self.ids.newscontent.text = "説明なし(" + update_date  + ")"
        # リンク先の表示
        if(self.news_list.entries[self.news_cnt].link != ""):
            self.ids.newslink.text = self.news_list.entries[self.news_cnt].link
        else:
            self.ids.newslink.text = ""
        if(self.ids.autoplay.active):
            # ニュースの表示時間のリセットは、スケジュールを一度キャンセルし再度設定
            try:
                self.dispnews_event.cancel()
            except:
                print("failed to start dispnews_event")
            else:
                self.dispnews_event=Clock.schedule_interval(self.display_news_callback,self.news_interval)      # 30秒間隔で次のニュースを表示

    # 終了ダイアログ
    def exit_dialog(self):
        popup = PopupExitDialog()
        popup.open()

# アプリの定義
class NewsPanelApp(App):  
    def __init__(self, **kwargs):
        super(NewsPanelApp,self).__init__(**kwargs)
        self.title="ニュースリーダー"                 # ウィンドウタイトル名

# メインの定義
if __name__ == '__main__':
    NewsPanelApp().run()                             # クラスを指定

Builder.load_file('newspanel.kv')                    # kvファイル名

