# ==============================================================================
# ЧАСТИНА КОДУ 1 (Для Скріншоту 1 / Рис. 2 у звіті)
# ==============================================================================
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from copy import deepcopy


class TaskPriority(Enum):
    LOW = (1, "Низький")
    MEDIUM = (2, "Середній")
    HIGH = (3, "Високий")
    CRITICAL = (4, "Критичний")

    def __init__(self, level: int, label: str):
        self.level = level
        self.label = label


class TaskStatus(Enum):
    TODO = "До виконання"
    IN_PROGRESS = "В роботі"
    DONE = "Виконано"
    EXPIRED = "Expired (Прострочено)"


@dataclass
class Employee:
    """Сутність виконавця завдання проєкту"""
    full_name: str
    position: str


@dataclass
class Project:
    """Сутність програмного проєкту"""
    name: str
    code: str


class Task:
    """Базовий клас завдання програмного проєкту"""
    def __init__(self, title: str, assignee: Employee, priority: TaskPriority, base_hours: float):
        self.__id = str(uuid.uuid4())[:6]
        self.title = title
        self.assignee = assignee
        self.priority = priority
        self.status = TaskStatus.TODO
        self.base_hours = base_hours

    @property
    def task_id(self) -> str:
        return self.__id

    @property
    def base_hours(self) -> float:
        return self.__base_hours

    @base_hours.setter
    def base_hours(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Час виконання повинен бути числом!")
        if value <= 0:
            raise ValueError("Час виконання повинен бути більшим за 0 годин!")
        self.__base_hours = float(value)

    def estimate_duration(self) -> float:
        return round(self.__base_hours, 2)

    # --- Магічні методи рядкового представлення ---
    def __str__(self) -> str:
        return (
            f"[{self.__id}] '{self.title}' | Пріоритет: {self.priority.label} | "
            f"Статус: {self.status.value} | Виконавець: {self.assignee.full_name} | "
            f"Оцінка: {self.estimate_duration()} год."
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id='{self.__id}', title='{self.title}', "
            f"priority=TaskPriority.{self.priority.name}, status=TaskStatus.{self.status.name}, "
            f"hours={self.estimate_duration()})"
        )

    # --- Магічні методи порівняння за пріоритетом ---
    def __eq__(self, other) -> bool:
        if not isinstance(other, Task):
            return False
        return (self.priority.level == other.priority.level and
                self.estimate_duration() == other.estimate_duration())

    def __lt__(self, other) -> bool:
        if not isinstance(other, Task):
            raise TypeError("Порівнювати можна лише об'єкти класу Task!")
        if self.priority.level != other.priority.level:
            return self.priority.level < other.priority.level
        return self.estimate_duration() < other.estimate_duration()

    # --- Магічний метод "Математика бізнесу" (Перевантаження +) ---
    def __add__(self, other):
        # 1. Додавання числа: збільшення оцінки часу на буферний резерв (повертає НОВИЙ об'єкт)
        if isinstance(other, (int, float)):
            if other < 0:
                raise ValueError("Додатковий резерв часу не може бути від'ємним!")
            new_task = deepcopy(self)
            new_task.base_hours = self.base_hours + float(other)
            return new_task

        # 2. Додавання двох завдань: об'єднання у спільне композитне завдання (повертає НОВИЙ об'єкт)
        if isinstance(other, Task):
            max_priority = self.priority if self.priority.level >= other.priority.level else other.priority
            total_hours = self.estimate_duration() + other.estimate_duration()
            combined_title = f"{self.title} + {other.title}"
            return Task(
                title=combined_title,
                assignee=self.assignee,
                priority=max_priority,
                base_hours=total_hours
            )
        raise TypeError("До завдання можна додавати лише інше завдання (Task) або число годин (int/float)!")


# ==============================================================================
# ЧАСТИНА КОДУ 2 (Для Скріншоту 2 / Рис. 3 у звіті)
# ==============================================================================
class DevelopmentTask(Task):
    """Завдання на розробку функціоналу"""
    def __init__(self, title: str, assignee: Employee, priority: TaskPriority, base_hours: float, complexity_coef: float):
        super().__init__(title, assignee, priority, base_hours)
        if complexity_coef < 1.0:
            raise ValueError("Коефіцієнт складності розробки не може бути меншим за 1.0!")
        self.complexity_coef = float(complexity_coef)

    def estimate_duration(self) -> float:
        return round(self.base_hours * self.complexity_coef, 2)


class BugTask(Task):
    """Завдання на виправлення помилки (багу)"""
    def __init__(self, title: str, assignee: Employee, priority: TaskPriority, base_hours: float, severity_level: int):
        super().__init__(title, assignee, priority, base_hours)
        if not (1 <= severity_level <= 5):
            raise ValueError("Рівень критичності багу має бути в межах від 1 до 5!")
        self.severity_level = severity_level

    def estimate_duration(self) -> float:
        return round(self.base_hours + (self.severity_level * 1.5), 2)


class TestingTask(Task):
    """Завдання на тестування"""
    def __init__(self, title: str, assignee: Employee, priority: TaskPriority, base_hours: float, test_cases_count: int):
        super().__init__(title, assignee, priority, base_hours)
        if test_cases_count <= 0:
            raise ValueError("Кількість тест-кейсів має бути додатною!")
        self.test_cases_count = test_cases_count

    def estimate_duration(self) -> float:
        return round(self.base_hours + (self.test_cases_count * 0.25), 2)


class TaskStatusTransaction:
    """Контекстний менеджер для зміни статусу завдання з контролем Time-Out"""
    def __init__(self, task: Task, target_status: TaskStatus, timeout_sec: float = 2.0):
        self.task = task
        self.target_status = target_status
        self.timeout_sec = timeout_sec
        self.previous_status = None
        self.start_time = 0.0

    def __enter__(self) -> Task:
        self.previous_status = self.task.status
        self.start_time = time.time()
        print(f"\n-> [ENTER] Початок транзакції для завдання [{self.task.task_id}] '{self.task.title}'.")
        print(f"   Поточний статус: {self.previous_status.value}. Ліміт часу: {self.timeout_sec} сек.")
        self.task.status = TaskStatus.IN_PROGRESS
        return self.task

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed = round(time.time() - self.start_time, 2)
        if exc_type is not None:
            self.task.status = self.previous_status
            print(f"<- [EXIT | ПОМИЛКА] Виявлено збій: {exc_val}!")
            print(f"   Виконано відкат (Rollback) статусу до: '{self.task.status.value}'.")
            return False

        if elapsed > self.timeout_sec:
            self.task.status = TaskStatus.EXPIRED
            print(f"<- [EXIT | TIME-OUT] Час операції ({elapsed} с) перевищив ліміт ({self.timeout_sec} с)!")
            print(f"   Статус завдання автоматично змінено на: '{self.task.status.value}'.")
        else:
            self.task.status = self.target_status
            print(f"<- [EXIT | УСПІХ] Операція тривала {elapsed} с. Новий статус: '{self.task.status.value}'.")
        return False


class ProjectManager:
    """Клас-менеджер проєкту з підтримкою кастомної ітерації та індексації"""
    def __init__(self, project: Project):
        self.project = project
        self._tasks: list[Task] = []

    def add_task(self, task: Task):
        self._tasks.append(task)
        print(f"[Успіх] До проєкту '{self.project.name}' додано: {task}")

    def __len__(self) -> int:
        return len(self._tasks)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._tasks[key]
        if isinstance(key, str):
            for task in self._tasks:
                if task.task_id == key:
                    return task
            raise KeyError(f"Завдання з ID '{key}' не знайдено!")
        raise TypeError("Ключем пошуку має бути індекс (int) або ID завдання (str)!")

    def __iter__(self):
        """Обмеження ітерації: повертає лише невиконані завдання за спаданням пріоритету"""
        active_tasks = [t for t in self._tasks if t.status != TaskStatus.DONE]
        sorted_tasks = sorted(active_tasks, reverse=True)
        return iter(sorted_tasks)


# ==============================================================================
# ЧАСТИНА КОДУ 3 (Для Скріншоту 3 / Рис. 4 у звіті)
# ==============================================================================
if __name__ == "__main__":
    project = Project("Система електронного документообігу", "SED-2026")
    manager = ProjectManager(project)

    # Попередньо створені об'єкти для швидкого тестування
    emp_dev = Employee("Ісайкін І.М.", "Backend Developer")
    emp_qa = Employee("Коваленко О.В.", "QA Engineer")

    t1 = DevelopmentTask("Розробка модуля авторизації", emp_dev, TaskPriority.HIGH, 10.0, complexity_coef=1.5)
    t2 = BugTask("Виправлення витоку пам'яті в кеші", emp_dev, TaskPriority.CRITICAL, 4.0, severity_level=4)
    t3 = TestingTask("Написання інтеграційних тестів", emp_qa, TaskPriority.LOW, 5.0, test_cases_count=12)
    manager.add_task(t1)
    manager.add_task(t2)
    manager.add_task(t3)

    while True:
        print("\n=== Система управління завданнями проєкту (ЛР №4) ===")
        print("1. Демонстрація __str__ та __repr__ (користувацький та технічний вивід)")
        print("2. Математика бізнесу (__add__) та порівняння завдань (__lt__, __eq__)")
        print("3. Кастомна ітерація (__iter__): невиконані завдання за пріоритетом")
        print("4. Тест контекстного менеджера (Успіх / Time-Out / Помилка з відкатом)")
        print("5. Додати власне завдання вручну")
        print("6. Вийти з програми")
        choice = input("Ваш вибір (1-6): ").strip()

        try:
            if choice == "1":
                print("\n--- 1. Виклик print(task) -> спрацьовує __str__ ---")
                for i in range(len(manager)):
                    print(manager[i])
                print("\n--- 2. Вивід колекції у списку -> спрацьовує __repr__ ---")
                print([manager[i] for i in range(len(manager))])

            elif choice == "2":
                print("\n--- Порівняння завдань за пріоритетом (__lt__, __eq__) ---")
                print(f"Завдання 1: {t1.title} ({t1.priority.label}, {t1.estimate_duration()} год)")
                print(f"Завдання 2: {t2.title} ({t2.priority.label}, {t2.estimate_duration()} год)")
                print(f"Чи Завдання 2 має вищий пріоритет за Завдання 1 (t2 > t1)? -> {t2 > t1}")
                print(f"Чи рівні завдання (t1 == t2)? -> {t1 == t2}")

                print("\n--- Математика бізнесу: Оператор + (__add__) ---")
                buffered_t1 = t1 + 3.5
                print(f"Додавання резерву (t1 + 3.5 год):\n  Оригінал: {t1}\n  Новий об'єкт: {buffered_t1}")
                merged_task = t1 + t3
                print(f"Об'єднання двох завдань (t1 + t3):\n  Новий об'єкт: {merged_task}")

            elif choice == "3":
                print(f"\n--- Ітерація по ProjectManager (всього у базі: {len(manager)} завд.) ---")
                print("(Виводяться лише невиконані завдання від найвищого пріоритету до найнижчого):")
                for idx, task in enumerate(manager, 1):
                    print(f"{idx}. {task}")

            elif choice == "4":
                print("\nОберіть підсценарій контекстного менеджера (with):")
                print("1 - Штатне завершення (швидке виконання, статус -> Виконано)")
                print("2 - Сценарій 'Time-Out' (затримка time.sleep, статус -> Expired)")
                print("3 - Аварійний збій всередині блоку (відкат статусу до початкового)")
                sub = input("Підсценарій (1-3): ").strip()

                if sub == "1":
                    with TaskStatusTransaction(t3, TaskStatus.DONE, timeout_sec=2.0) as active_task:
                        print(f"   [Робота в блоці with] Статус під час роботи: {active_task.status.value}")
                        time.sleep(0.5)
                    print(f"Фінальний стан t3: {t3}")

                elif sub == "2":
                    with TaskStatusTransaction(t1, TaskStatus.DONE, timeout_sec=1.5) as active_task:
                        print(f"   [Робота в блоці with] Імітація довгого виконання (2.2 сек)...")
                        time.sleep(2.2)
                    print(f"Фінальний стан t1: {t1}")

                elif sub == "3":
                    try:
                        with TaskStatusTransaction(t2, TaskStatus.DONE, timeout_sec=3.0) as active_task:
                            print(f"   [Робота в блоці with] Статус під час роботи: {active_task.status.value}")
                            raise RuntimeError("Відсутнє з'єднання з сервером репозиторію!")
                    except RuntimeError as err:
                        print(f"[Перехоплено в меню]: {err}")
                    print(f"Фінальний стан t2 після відкату: {t2}")

            elif choice == "5":
                title = input("Назва завдання: ").strip()
                hours = float(input("Базовий час (год): "))
                coef = float(input("Коефіцієнт складності (>= 1.0): "))
                new_t = DevelopmentTask(title, emp_dev, TaskPriority.MEDIUM, hours, coef)
                manager.add_task(new_t)

            elif choice == "6":
                print("Завершення роботи програми.")
                break
            else:
                print("[Помилка] Оберіть опцію від 1 до 6.")

        except (ValueError, TypeError, KeyError) as e:
            print(f"\n[Помилка валідації або типізації]: {e}")