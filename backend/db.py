import sqlite3, os
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "library.sqlite")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'staff', password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tokens(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS authors(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, country TEXT, born INTEGER, bio TEXT);
CREATE TABLE IF NOT EXISTS books(id INTEGER PRIMARY KEY, title TEXT NOT NULL, author_id INTEGER NOT NULL,
  genre TEXT, year INTEGER, copies INTEGER NOT NULL DEFAULT 1, FOREIGN KEY(author_id) REFERENCES authors(id));
CREATE TABLE IF NOT EXISTS loans(id INTEGER PRIMARY KEY, book_id INTEGER NOT NULL, member TEXT NOT NULL,
  issued TEXT NOT NULL, due TEXT NOT NULL, returned TEXT, FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE);
"""

AUTHORS = """Harper Lee|USA|1926|Pulitzer-winning novelist known for exploring justice and race in the American South.
George Orwell|UK|1903|Essayist and novelist who wrote sharply about totalitarianism.
Jane Austen|UK|1775|Witty chronicler of English country society and romance.
Gabriel García Márquez|Colombia|1927|Nobel laureate and master of magical realism.
Paulo Coelho|Brazil|1947|Bestselling author of spiritual, allegorical fiction.
Agatha Christie|UK|1890|The best-selling crime novelist of all time.
J.K. Rowling|UK|1965|Creator of the Harry Potter series.
Haruki Murakami|Japan|1949|Surreal, melancholic fiction loved worldwide.
Yuval Noah Harari|Israel|1976|Historian exploring the story of humankind.
Chinua Achebe|Nigeria|1930|Father of modern African literature."""

BOOKS = """To Kill a Mockingbird|Harper Lee|Fiction|1960|3
1984|George Orwell|Dystopian|1949|4
Animal Farm|George Orwell|Satire|1945|2
Pride and Prejudice|Jane Austen|Romance|1813|3
Emma|Jane Austen|Romance|1815|2
One Hundred Years of Solitude|Gabriel García Márquez|Magical Realism|1967|2
Love in the Time of Cholera|Gabriel García Márquez|Romance|1985|2
The Alchemist|Paulo Coelho|Adventure|1988|5
Murder on the Orient Express|Agatha Christie|Mystery|1934|3
And Then There Were None|Agatha Christie|Mystery|1939|3
Harry Potter and the Philosopher's Stone|J.K. Rowling|Fantasy|1997|6
Harry Potter and the Chamber of Secrets|J.K. Rowling|Fantasy|1998|4
Norwegian Wood|Haruki Murakami|Fiction|1987|2
Kafka on the Shore|Haruki Murakami|Fantasy|2002|2
Sapiens|Yuval Noah Harari|History|2011|4
Homo Deus|Yuval Noah Harari|History|2015|3
Things Fall Apart|Chinua Achebe|Fiction|1958|3
Go Set a Watchman|Harper Lee|Fiction|2015|1"""

def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    if not conn.execute("SELECT 1 FROM users").fetchone():
        for u, n, r, p in [("admin", "Administrator", "admin", "admin123"), ("staff", "Library Staff", "staff", "staff123")]:
            conn.execute("INSERT INTO users(username,name,role,password_hash) VALUES (?,?,?,?)", (u, n, r, generate_password_hash(p)))
        for line in AUTHORS.splitlines():
            n, c, b, bio = line.split("|")
            conn.execute("INSERT INTO authors(name,country,born,bio) VALUES (?,?,?,?)", (n, c, int(b), bio))
        for line in BOOKS.splitlines():
            t, a, g, y, c = line.split("|")
            aid = conn.execute("SELECT id FROM authors WHERE name=?", (a,)).fetchone()["id"]
            conn.execute("INSERT INTO books(title,author_id,genre,year,copies) VALUES (?,?,?,?,?)", (t, aid, g, int(y), int(c)))
        day = lambda n: (date.today() + timedelta(days=n)).isoformat()
        for book_id, member, off in [(2, "Aisha Khan", -12), (8, "Rahul Verma", -3), (11, "Meera Nair", 5),
                                     (15, "Daniel Cruz", 9), (1, "Sara Ali", 12), (9, "Tom Becker", 2)]:
            conn.execute("INSERT INTO loans(book_id,member,issued,due) VALUES (?,?,?,?)", (book_id, member, day(off - 14), day(off)))
    conn.commit(); conn.close()
