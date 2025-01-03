from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QTableWidget, QTableWidgetItem, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, 
                             QInputDialog, QTimeEdit, QDateTimeEdit)
from PyQt5.QtCore import Qt, QSize, QDate, QTime, QDateTime
import sys
import mysql.connector
from mysql.connector import Error
import datetime

class QuanLy(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quan Ly Lessons")
        self.setFixedSize(QSize(800, 300))

        self.thu = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.thoi_gian = ["Morning", "Afternoon", "Evening"]
        self.table = QTableWidget(3, 7)
        self.table.setHorizontalHeaderLabels(self.thu)
        self.table.setVerticalHeaderLabels(self.thoi_gian)

        self.lesson_name_input = QInputDialog()
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.date_time_edit = QDateTimeEdit()
        self.date_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_time_edit.setCalendarPopup(True)

        self.button_add = QPushButton("Them buoi hoc")
        self.button_add.clicked.connect(self.add_lesson)
        self.button_remove = QPushButton("Xoa buoi hoc")
        self.button_remove.clicked.connect(self.remove_lesson)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Time:"))
        input_layout.addWidget(self.time_edit)
        input_layout.addWidget(QLabel("Date and Time:"))
        input_layout.addWidget(self.date_time_edit)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(input_layout)
        layout.addWidget(self.button_add)
        layout.addWidget(self.button_remove)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.db_connection = self.connect_to_database()
        if self.db_connection:
            self.load_lessons_from_database()

    def connect_to_database(self):
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="10112005",
                database="quanli"
            )
            return connection
        except Error as e:
            QMessageBox.critical(self, "Database Error", f"Error connecting to database: {e}")
            return None

    def load_lessons_from_database(self):
        if not self.db_connection:
            return

        cursor = self.db_connection.cursor()
        try:
            cursor.execute("SELECT name_lesson, times, days FROM lessons")
            lessons = cursor.fetchall()

            for lesson in lessons:
                if len(lesson) >= 3:
                    name, time, day = lesson[0], lesson[1], lesson[2]
                    if isinstance(day, datetime.datetime) and isinstance(time, datetime.time):
                        day_index = day.weekday()
                        time_index = self.get_time_index(time)
                        self.table.setItem(time_index, day_index, QTableWidgetItem(name))
                    else:
                        print(f"Skipping invalid lesson data: {lesson}")
                else:
                    print(f"Skipping incomplete lesson data: {lesson}")
        except Error as e:
            QMessageBox.warning(self, "Database Error", f"Error loading lessons: {e}")
        finally:
            cursor.close()

    def get_time_index(self, time):
        if isinstance(time, datetime.time):
            if time < datetime.time(12, 0):
                return 0  # Morning
            elif time < datetime.time(18, 0):
                return 1  # Afternoon
            else:
                return 2  # Evening
        else:
            print(f"Invalid time format: {time}")
            return 0  # Default to Morning if invalid

    def add_lesson(self):
        lesson, ok = QInputDialog.getText(self, "Add Lesson", "Enter lesson name:")
        if ok and lesson:
            time = self.time_edit.time()
            date_time = self.date_time_edit.dateTime()
            
            day_index = date_time.date().dayOfWeek() - 1  # Qt uses Monday as 1, we use 0
            time_index = self.get_time_index(time.toPyTime())

            if not self.db_connection:
                QMessageBox.warning(self, "Database Error", "Not connected to the database.")
                return

            try:
                cursor = self.db_connection.cursor()
                query = "INSERT INTO lessons (name_lesson, times, days) VALUES (%s, %s, %s)"
                values = (lesson, time.toPyTime(), date_time.toPyDateTime())
                cursor.execute(query, values)
                self.db_connection.commit()
                self.table.setItem(time_index, day_index, QTableWidgetItem(lesson))
                QMessageBox.information(self, "Success", "Lesson added successfully!")
            except Error as e:
                QMessageBox.warning(self, "Database Error", f"Error adding lesson: {e}")
            finally:
                cursor.close()

    def remove_lesson(self):
        current_item = self.table.currentItem()
        if current_item is not None:
            row = self.table.currentRow()
            col = self.table.currentColumn()
            lesson = current_item.text()

            if not self.db_connection:
                QMessageBox.warning(self, "Database Error", "Not connected to the database.")
                return

            try:
                cursor = self.db_connection.cursor()
                query = "DELETE FROM lessons WHERE name_lesson = %s"
                values = (lesson,)
                cursor.execute(query, values)
                self.db_connection.commit()
                self.table.setItem(row, col, None)
                QMessageBox.information(self, "Success", "Lesson removed successfully!")
            except Error as e:
                QMessageBox.warning(self, "Database Error", f"Error removing lesson: {e}")
            finally:
                cursor.close()
        else:
            QMessageBox.warning(self, "Warning", "Please select a cell to remove.")

    def closeEvent(self, event):
        if self.db_connection:
            self.db_connection.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuanLy()
    window.show()
    sys.exit(app.exec_())

