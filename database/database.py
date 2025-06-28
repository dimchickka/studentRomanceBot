import sqlite3
import os
from queue import Queue
from threading import Lock
import random


class Database:
    def __init__(self, dbPath: str = 'database/bot.db', poolSize: int = 5):
        os.makedirs(os.path.dirname(dbPath), exist_ok=True)

        self.dbPath = dbPath
        self.poolSize = poolSize
        self.lock = Lock()
        self.connectionPool = Queue(maxsize=poolSize)

        self._initPoolAndCheckTable()

    def _initPoolAndCheckTable(self):
        """Инициализирует пул соединений и проверяет таблицу"""
        with self.lock:
            temp_conn = self._createNewConnection()
            try:
                cursor = temp_conn.cursor()

                # Проверяем существование таблицы
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if not cursor.fetchone():
                    # Создаем таблицу
                    cursor.execute('''
                        CREATE TABLE users (
                            id INTEGER PRIMARY KEY,
                            username TEXT,
                            sex INTEGER CHECK(sex IN (0, 1)),
                            city TEXT,
                            university TEXT,
                            course TEXT,
                            age INTEGER,
                            description TEXT,
                            photo TEXT
                        )
                    ''')

                    # ✅ Добавляем индексы для ускорения фильтрации
                    cursor.execute('CREATE INDEX idx_city ON users(city)')
                    cursor.execute('CREATE INDEX idx_sex ON users(sex)')
                    cursor.execute('CREATE INDEX idx_university ON users(university)')
                    cursor.execute('CREATE INDEX idx_city_sex ON users(city, sex)')
                    cursor.execute('CREATE INDEX idx_university_sex ON users(university, sex)')

                    temp_conn.commit()

                # Инициализируем пул соединений
                for _ in range(self.poolSize):
                    conn = self._createNewConnection()
                    self.connectionPool.put(conn)

            finally:
                temp_conn.close()

    def _createNewConnection(self):
        conn = sqlite3.connect(self.dbPath, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def getConnection(self):
        try:
            return self.connectionPool.get_nowait()
        except:
            return self._createNewConnection()

    def returnConnection(self, conn):
        if conn:
            try:
                conn.rollback()
                if self.connectionPool.qsize() < self.poolSize:
                    self.connectionPool.put_nowait(conn)
                else:
                    conn.close()
            except:
                conn.close()

    def addUser(self, userId: int, username: str, sex: bool, city: str, university: str, course: str,
                age: int, description: str, photo: str = None):
        conn = None
        try:
            conn = self.getConnection()
            cursor = conn.cursor()

            sex_int = 1 if sex else 0
            photo_value = photo if photo else None
            params = (
                int(userId),
                str(username),
                int(sex_int),
                str(city),
                str(university),
                str(course),
                int(age),
                str(description),
                photo_value
            )
            cursor.execute('''
                INSERT OR REPLACE INTO users
                (id, username, sex, city, university, course, age, description, photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', params)
            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.returnConnection(conn)

    def getMatchingUsers(self, viewer_id: int = None, sex: int = None, city: str = None, university: str = None):
        conn = self.getConnection()
        try:
            cursor = conn.cursor()

            query = 'SELECT id FROM users WHERE 1=1'
            params = []

            if viewer_id is not None:
                query += ' AND id != ?'
                params.append(viewer_id)

            if sex is not None:
                query += ' AND sex = ?'
                params.append(sex)

            if city:
                query += ' AND city = ?'
                params.append(city)

            if university:
                query += ' AND university = ?'
                params.append(university)

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            return [row[0] for row in rows]

        finally:
            self.returnConnection(conn)

    def getUserById(self, user_id: int):
        conn = self.getConnection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT * FROM users
                WHERE id = ?
                ''',
                (user_id,)
            )
            return cursor.fetchone()
        finally:
            self.returnConnection(conn)

    def getSexById(self, user_id: int) -> int | None:
        conn = self.getConnection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT sex FROM users WHERE id = ?
                ''',
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            self.returnConnection(conn)

    def getFieldById(self, user_id: int, field: str):
        conn = self.getConnection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {field} FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            self.returnConnection(conn)

    def getAllUserIds(self):
        conn = self.getConnection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT id FROM users
                '''
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]  # Извлекаем только id
        finally:
            self.returnConnection(conn)

    def deleteUserById(self, user_id: int):
        conn = self.getConnection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
        finally:
            self.returnConnection(conn)

    def update_user_description(self, user_id: int, new_description: str):
        """Обновляет описание пользователя в базе данных"""
        conn = None
        try:
            conn = self.getConnection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users 
                SET description = ?
                WHERE id = ?
            ''', (str(new_description), int(user_id)))

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            return False

        finally:
            if conn:
                self.returnConnection(conn)


# ✅ Проверка через main
if __name__ == "__main__":
    db = Database()

    fake_user = {
        "userId": random.randint(10000, 99999),
        "username": "TestUser",
        "sex": random.choice([True, False]),
        "city": "Москва",
        "university": "МГТУ им. Баумана",
        "course": "2",
        "age": random.randint(18, 25),
        "description": "Просто тестовая анкета",
        "photo": None
    }

    db.addUser(**fake_user)
