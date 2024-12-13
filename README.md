## Проект: Расчет рациона питания на неделю на основе антропометрических данных

Этот проект предоставляет инструмент для расчета оптимального рациона питания на основе калорийности, исходя из антропометрических данных пользователя и списка продуктова конкретного продуктового магазина.

### Описание проекта
**Pipline**:  
1. Сбор данных с использованием веб-скрепинга на основе продуктового ритейлера  
2. Оценка полученных товаров с использованием LLM (Large Language Model)
3. Проведение разведывательного анализа данных (EDA)
4. Определение и обоснование метрик оценки качества проекта
5. Создание базы данных в SQLite
6. Разработка и внедрение алгоритма для подсчёта локальной калорийности человека  
7. Разработка и внедрение алгоритма для составления итогового списка
8. Применение Prefect для оптимизации процессов

Программа предоставляет список продуктов, определяет калорийность каждого продукта и рассчитывает оптимальный рацион (список конкретных продуктов) на основе антропометрических данных пользователя (пол, возраст, вес, рост, коэффициент физической активности).

### Структура проекта
project_root/  
* ai.py # определение "качества" продуктов на основе качества макронутриентов, полезности, потребность организмом и присваивает товарам "оценки продукта" от 1 ├ до 10  
* algorithm.py # ранжирование продуктов и предоставление их списком на основе введённых антропометрических данных  
* productRepository.py # web-scrapping продуктов с сайта магазина "Пятёрочка"
* config.py # название всех файлов в одном месте
* database.py # в перспективе сохраняет базу данных; переводит products.сsv в processed_products.csv
* --------------------------------------------------------------
* categories.csv #Список категорий и подкатегорий продуктов
* row_products.csv #Данные с сайта
* product.csv # row_products.csv без лишних столбцов
* processed_products # products.csv в рабочем виде без "оценки качества продуктов" (Score)
* product_with_scores.csv # processed_products со Score
* --------------------------------------------------------------
* EDA.ipynd #процесс подготовки и анализа данных от categories.csv до products_with_scores.csv
* Metrics.ipynd # обоснование и визуализация метрик для оценки качества готового DF



### Prerequisites
- Python
- GigaChat
- SQLite

### Метрики
## Оценка качества полученных данных определяется на основе анализа параметра Score.

1. Метрика **"Оценка качества продукта"**  

Предполагает, что программа автоматически оценивает качество продукта на основе определённых параметров и вычисляет разницу межде Score_X и Score_y.

Для проверки точности работы программы мы выбираем случайную выборку из 100 продуктов и сравниваем их автоматически рассчитанные значениями Score с размеченными вручную оценками Our_Score. Если различие между этими оценками незначительно, это свидетельствует о корректной работе алгоритма

2. Метрика **"Оценка качества алгоритма на основе содержания белков"**

Предполагается, что продукты с высоким содержанием белков должны получать высокие оценки качества (Score > 6). Мы проверяем это предположение, анализируя нутриентный состав продуктов (белки, жиры, углеводы). Продукты, у которых соотношение белков значительно выше по сравнению с другими нутриентами, будут считаться высокобелковыми. Затем мы оцениваем, как часто такие продукты получают высокие оценки (Score>6), и визуализируем результаты.
Если таких продуктов больше 90%, то механизм оценки качества продуктов удовлетворяет задач программы

3. Метрика **"Соотношение цена-качество"**

Мы предполагаем, что высокий показатель качества продукта (Score > 7) можно достичь без значительных затрат на единицу массы продукта. То есть существует достаточное количество продуктов, у которых соотношение "цена/масса" остается умеренным при высоком Score.

4. Метрика **"Топ 100 товаров на основе рейтинга и их калорийность"**

Цель метрики проверить наличие корреляции между калорийностью продуктов и их рейтингом (Score). Мы предполагаем, что высококалорийные продукты не должны автоматически попадать в категорию продуктов с высоким Score.
Основная гипотеза:
Алгоритм не связывает высокую калорийность с высоким значением Score. Это подтверждается, если продукты, входящие в топ-100 по Score, в значительной степени не пересекаются с продуктами, входящими в топ-100 по калорийности.

### Пример использования

python algorithm.py <пол> <возраст> <вес> <рост> <коэффициентфизическойактивности>

**Пример:**

python algorithm.py Мужчина 30 80 180 1.55

Эта команда запустит программу с указанными параметрами.  Программа выведет список продуктов, их калорийность, количественные значения БЖУ каждого продукта и общую калорийность рациона.


**Обязательные параметры ввода:**

`пол` (Мужчина/Женщина)  
`возраст` (целое число)  
`вес` (в кг, вещественное число)  
`рост` (в см, вещественное число)  
`коэффициент_физической_активности` (вещественное число, например, 1.2-1.9)

**Формат вывода:**

Программа выведет список продуктов в формате:
Название продукта, масса продукта, БЖУ, комплексная оценка товара
Также в выводе программы есть калорийность с учётом необходимого количества калорий

"Результат расчёта:
С учётом вашей активности, вам требуется: 2846.00 калорий/день.  
Weekly menu generated successfully in 6927 attempts!  
Weekly Menu:  
- Блюдо готовое Фондю Эменталь замороженное 4 сезона 600г: 600.00g/ml, Protein: 47.40g, Fat: 61.20g, Carbs: 79.80g, Score: 3.33
- ...  
- Манго спелое Египет: 700.00g/ml, Protein: 3.50g, Fat: 2.10g, Carbs: 80.50g, Score: 9.00 

Total Nutrients for the Week:  
Calories: 21717.75 kcal  
Protein: 751.05 g  
Fat: 695.02 g  
Carbs: 3036.32 g   "

### Авторы
Гурьев Георгий Александрович