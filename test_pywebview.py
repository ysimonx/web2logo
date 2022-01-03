import webview
import sys

"""
This example demonstrates how to retrieve a DOM element
"""


def get_elements(window):
    html = window.get_elements('html')
   
    print(html)
    window.destroy()
    sys.exit()
    

if __name__ == '__main__':
    html = """
      <html>
        <body>
          <h1 id="heading">Heading</h1>
          <div class="content">Content 1</div>
          <div class="content">Content 2</div>
        </body>
      </html>
    """
    window = webview.create_window('Hello world', 'https://cdiscount.com')
    webview.start(get_elements, window)

