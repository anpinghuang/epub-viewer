import io
import re
from flask import Flask, render_template, request, url_for, redirect
from ebooklib import epub
import ebooklib
import os
import tempfile

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB maximum file size allowed
app.config['UPLOAD_EXTENSIONS'] = ['.epub']
app.config['UPLOADS'] = {}

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            return render_template('upload.html', error=True)
        file_contents = io.BytesIO()
        uploaded_file.save(file_contents)
        app.config['UPLOADS'][filename] = file_contents
        return redirect(url_for('view_epub', filename=filename))
    return render_template('upload.html', error=True)

@app.route('/view_epub/<filename>')
def view_epub(filename):
    if filename not in app.config['UPLOADS']:
        return redirect(url_for('index'))
    book_content = app.config['UPLOADS'][filename].getvalue()
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(book_content)
        temp.flush()
        book = epub.read_epub(temp.name)
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content().decode('utf-8')
        clean_text = re.sub('<[^<]+?>', '', content)  # remove html tags
        clean_text = clean_text.replace('\n', '')  # remove new line characters
        clean_text = clean_text.strip()  # remove leading/trailing whitespaces
        chapters.append(clean_text)

    # generate chapter links based on chapter titles
    chapter_links = [f'#{index}' for index in range(1, len(chapters) + 1)]

    return render_template('view_epub.html', title=book.get_metadata('DC', 'title'), chapters=chapters, chapter_links=chapter_links, enumerate=enumerate, book=book)

if __name__ == '__main__':
    app.run(debug=True)
