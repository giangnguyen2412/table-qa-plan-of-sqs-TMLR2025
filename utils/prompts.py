
# TABFACT


general_natural_language_plan_demo = """
We are working with a tabular dataset. 
Your task is to develop a step-by-step plan to verify if a given statement is TRUE or FALSE or to find the correct answer based on a given table. 
There exists data where smaller values indicate better, greater, or more favorable conditions, such as rankings, times, error rates, etc.

Here are example plans you can refer to:

### Table:
table caption: 2005 tournament results
/*
col : id | name | hometown | score
row 1 : 1 | alice | new york | 85
row 2 : 2 | bob | los angeles | 90
row 3 : 3 | charlie | chicago | 75
row 4 : 4 | dave | new york | 88
row 5 : 5 | eve | los angeles | 92
*/
Query: in 2005 tournament, bob and charlie are both from chicago.
Plan:
1. Select rows where the 'name' is 'bob' or 'charlie'.
2. Select rows where 'hometown' is 'chicago'.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

### Table:
table caption: salary last year
/*
col : id | name | department | salary | years
row 1 : 1 | alice | it | $95,000 | 3
row 2 : 2 | bob | finance | $105,000 | 5
row 3 : 3 | charlie | marketing | $88,000 | 2
*/
Query: no employee earns more than $100,000.
Plan:
1. Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
2. Select rows where the 'num_salary' is greater than 100000.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: 2000 uk championship
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | e
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | +3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | +2
row 4 : t4 | james canpo | france | 35 + 45 = 80 | -2
*/
Query: james canpo is the only player from france
Plan:
1. Extract the number of players from france from the 'country' column then add column 'france_cnt' to existing table.
2. Select rows where 'france_cnt' is 1.
3. Select rows where 'player' is 'james canpo'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: olympic 2018; table tennis
/*
col : rank | athlete | time
row 1 : 1 | manjeet kaur (ind) | 52.17
row 2 : 2 | olga tereshkova (kaz) | 51.86
row 3 : 3 | pinki pramanik (ind) | 53.06
*/
Query: in table tennis of olympic 2018, there are at most 2 athletes from india.
Plan: 
1. Select rows where 'athlete' is 'ind' using LIKE function.
2. Use a `CASE` statement to return TRUE if the number of rows is smaller than or equal to 2, otherwise return FALSE.

### Table:
/*
col : id | name | hometown
row 1 : 1 | alice | new york
row 2 : 2 | bob | los angeles
row 3 : 3 | charlie | chicago
*/
Query: which players are from chicago?
Plan:
1. Select rows where the 'hometown' is 'chicago'.
2. Select the 'name' column.

### Table:
/*
col : id | name | score
row 1 : 1 | alice | 85
row 2 : 2 | bob | 90
row 3 : 3 | charlie | 75
*/
Query: what is the score of alice?
Plan:
1. Select rows where the 'name' is 'alice'.
2. Select the 'score' column.

### Table:
/*
col : id | name | salary
row 1 : 1 | alice | $95,000
row 2 : 2 | bob | $105,000
row 3 : 3 | charlie | $88,000
*/
Query: how many employees earn more than $100,000?
Plan:
1. Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
2. Select rows where the 'num_salary' is greater than 100000.
3. Count the number of rows.

### Table:
/*
col : id | name | salary
row 1 : 1 | alice | $95,000
row 2 : 2 | bob | $105,000
row 3 : 3 | charlie | $88,000
*/
Query: what is the average salary?
Plan:
1. Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
2. Calculate the average salary from the 'num_salary' column.

### Table:
/*
col : place | player | score
row 1 : 1 | hale irwin | 68 + 68 = 136
row 2 : 2 | fuzzy zoeller | 71 + 66 = 137
row 3 : t3 | david canipe | 69 + 69 = 138
*/
Query: who had the highest score?
Plan:
1. Extract the numerical score from the 'score' column then add column 'num_score' to existing table.
2. Order the table by 'num_score' in descending order.
3. Select row number 1.
4. Select the 'player' column.

### Table:
/*
col : place | player | score
row 1 : 1 | hale irwin | 68 + 68 = 136
row 2 : 2 | fuzzy zoeller | 71 + 66 = 137
row 3 : t3 | david canipe | 69 + 69 = 138
*/
Query: what is the highest score?
Plan:
1. Extract the numerical score from the 'score' column then add column 'num_score' to existing table.
2. Calculate the highest score from the 'num_score' column.

### Table:
/*
col : rank | athlete | time
row 1 : 1 | manjeet kaur (ind) | 52.17
row 2 : 2 | olga tereshkova (kaz) | 51.86
row 3 : 3 | pinki pramanik (ind) | 53.06
*/
Query: how many athletes from india participated in?
Plan:
1. Select rows where 'athlete' is 'ind' using LIKE function.
2. Count the number of rows.

### Table:
table caption: olympic 2018; table tennis
/*
col : rank | athlete | time
row 1 : 1 | manjeet kaur (ind) | 52.17
row 2 : 2 | olga tereshkova (kaz) | 51.86
row 3 : 3 | pinki pramanik (ind) | 53.06
*/
Query: manjeet had the highest rank in the competition.
Plan: 
1. Order the table by 'rank' in ascending order.
2. Select row number 1.
3. Select rows where 'athlete' is 'manjeet' using LIKE function.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: book sale
/*
col : author | genre | books_sold
row 1 : smith | fiction | 300
row 2 : doe | fiction | 400
row 3 : roe | non-fiction | 500
*/
Query: fiction is the best-selling genre.
Plan:
1. Order the table by 'books_sold' in descending order.
2. Select row number 1.
3. Select rows where 'genre' is 'fiction'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: book sale
/*
col : author | genre | books_sold
row 1 : smith | fiction | 300
row 2 : doe | fiction | 400
row 3 : roe | non-fiction | 500
*/
Query: the maximum number of books sold is 600.
Plan:
1. Order the table by 'books_sold' in descending order.
2. Select row number 1.
3. Select rows where 'books_sold' is 600.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: us open 2024
/*
col : game | venue | date | attendance
row 1 : 1 | orlando | 2024-11-23 | 52000
row 2 : 2 | new york | 2022-09-12 | 51000
row 3 : 3 | san jose | 2024-09-09 | 53000
*/
Query: the earliest game was played in orlando.
Plan: 
1. Order the table by 'date' in ascending order.
2. Select row number 1.
3. Select rows where 'venue' is 'orlando'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: opponents of wildcats
/*
col : game_id | venue | when | attendance | team | game
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic | away
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks | away
row 3 : 3 | orlando | 2024-09-11 | 50000 | tigers | away
*/
Query: all matches are on different dates
Plan:
1. Extract the number of distinct dates from the 'when' column then add column 'date_cnt' to existing table.
2. Select rows where 'date_cnt' is 3.
3. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: attendance record in 2024
*/
col : game | venue | date | attendance
row 1 : 1 | orlando | 2024-11-23 | 52000
row 2 : 2 | new york | 2022-09-12 | 51000
row 3 : 3 | san jose | 2024-09-09 | 53000
*/
Query: all the games are played in 2024
Plan: 
1. Extract the numerical year from the 'date' column then add column 'year' to existing table.
2. Select rows where 'year' is not 2024.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: attendance record in 2024
*/
col : game | venue | date | attendance
row 1 : 1 | orlando | 2024-11-23 | 52000
row 2 : 2 | new york | 2022-09-12 | 51000
row 3 : 3 | san jose | 2024-09-09 | 53000
*/
Query: the lowest attendance was 50000
Plan: 
1. Order the table by 'attendance' in ascending order.
2. Select row number 1.
3. Select rows where 'attendance' is 50000.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: final rankings and medals
/*
col : id | athlete | country | sport | medals
row 1 : 1 | alice | usa | swimming | 5
row 2 : 2 | bob | canada | hockey | 3
row 3 : 3 | charlie | australia | athletics | 2
*/
Query: there is no athlete from canada.
Plan:
1. Select rows where 'country' is 'canada'.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: final rankings 2009
/*
col : rank_sport | athlete | country | sport | medals
row 1 : 1 | alice | usa | swimming | 5
row 2 : 2 | bob | canada | hockey | 3
row 3 : 3 | charlie | australia | athletics | 2
row 4 : 4 | park | korea | gymnastics | 1
*/
Query: park has the lowest sport rank in 2009.
Plan:
1. Order the table by 'rank_sport' in descending order.
2. Select row number 1.
3. Select rows where 'athlete' is 'park'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: olympic rankings
/*
col : rank | total_medals | country | silver_medals | gold_medals
row 1 : 1 | 7 | usa | 2 | 5
row 2 : 2 | 7 | canada | 4 | 3
row 3 : 3 | 4 | australia | 2 | 2
*/
Query: canada has the highest number of silver medals.
Plan:
1. Order the table by 'silver_medals' in descending order.
2. Select row number 1.
3. Select rows where 'country' is 'canada'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: game results in 2024
/*
col : game_id | venue | date | attendance | team
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks
row 3 : 3 | san jose | 2024-09-09 | 35000 | sharks
*/
Query: no games were played in december.
Plan:
1. Extract the numerical month from the 'date' column then add column 'month' to existing table.
2. Select rows where 'month' is 12.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: list of winners
/*
col : id | player | country | sport | medals
row 1 : 1 | alice | usa | swimming | 5
row 2 : 2 | bob | canada | hockey | 3
row 3 : 3 | charlie | italia | athletics | 2
*/
Query: there are less than 2 players from italia in the list of winners.
Plan:
1. Select rows where 'country' is 'italia'.
2. Use a `CASE` statement to return TRUE if the number of rows is smaller than 2, otherwise return FALSE.

### Table:
table caption: opponents of wildcats
/*
col : game_id | venue | date | attendance | team
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks
row 3 : 3 | san jose | 2024-09-09 | 35000 | sharks
*/
Query: sharks was the opponent of the last game.
Plan:
1. Order the table by 'game_id' in descending order.
2. Select row number 1.
3. Select rows where 'team' is 'sharks'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: book sales
/*
col : iso/iec_standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2011) | 7
*/
Query: 2 standards are published in 2011.
Plan: 
1. Extract the year from the 'status' column then add column 'year_published' to existing table.
2. Select rows where 'year_published' is 2011.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

### Table:
table caption: book sales
/*
col : iso/iec_standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2011) | 7
*/
Query: the standard tr 19759 was released in 2005.
Plan: 
1. Extract the year from the 'status' column then add column 'year_published' to existing table.
2. Select rows where 'year_published' is 2005.
3. Select rows where 'iso/iec_standard' is 'tr 19759'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: 2018 financial report
/*
col : employee | department | money_per_hour
row 1 : alice | hr | 50.55
row 2 : bob | hr | 55.75
row 3 : charlie | it | 60.33
*/
Query: in 2018, alice earned the most money per hour.
Plan: 
1. Order the table by 'money_per_hour' in descending order.
2. Select row number 1.
3. Select rows where the 'employee' is 'alice'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: project list
/*
col : project_id | project_name | department | start_date | deadline
row 1 : 1 | migration | it | 2023-01-15 | 2024-03-01
row 2 : 2 | rebranding | marketing | 2023-06-20 | 2023-12-15
row 3 : 3 | audit | finance | 2023-09-10 | 2024-05-30
*/
Query: no project deadline is set before 2024.
Plan:
1. Extract the numerical year from the 'deadline' column then add column 'year' to existing table.
2. Select rows where the 'year' is before 2024.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 80
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/
Query: the average score of all employees is above 85.
Plan:
1. Extract the average of the 'score' column then add column 'avg_score' to existing table.
2. Select rows where the 'avg_score' is greater than 85.
3. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 80
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/
Query: eve had the most score among the listed players.
Plan:
1. Order the table by 'score' in descending order.
2. Select row number 1.
3. Select rows where the 'name' is 'eve'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 70
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 85
row 5 : 5 | eve | hr | 95
*/
Query: the difference between the highest and lowest scores is more than 20.
Plan:
1. Extract the difference between the maximum value and minimum value of the 'score' column then add column 'score_diff' to existing table.
2. Select rows where the 'score_diff' is greater than 20.
3. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 70
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/
Query: dave and bob together had the least amount of scores.
Plan:
1. Extract the minimum value of the 'score' column then add column 'min_score' to existing table.
2. Select rows where the 'score' is equal to 'min_score'.
3. Select rows where 'name' is 'dave' or 'bob'
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

### Table:
table caption: opponents of wildcats
/*
col : game_id | venue | date | attendance | team | game
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic | away
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks | away
row 3 : 3 | orlando | 2024-09-11 | 50000 | tigers | away
*/
Query: attendance of games in orlando is always over 50000.
Plan:
1. Select rows where 'venue' is 'orlando'.
2. Select rows where the 'attendance' is less than or equal to 50000.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: soccer ranking
/*
col : name | position | league_apps | league_goals | fa_cup_apps | fa_cup_goals | league_cup_apps | league_cup_goals | total_apps | total_goals
row 1 : mike maginan | df | 0 | 0 | 0 | 0 | 0 (1) | 0 | 0 (1) | 0
row 2 : tommy chris | df | 46 | 2 | 2 | 0 | 4 | 1 | 52 | 3
row 3 : johny lowe | mf | 39 (1) | 10 | 1 | 0 | 4 | 0 | 44 (1) | 10
row 4 : hannah denver | fw | 30 (8) | 17 | 2 | 0 | 3 | 1 | 35 (8) | 18
*/
Query: tommy chris played at mf
Plan:
1. Select rows where 'name' is 'tommy chris'.
2. Select rows where 'position' is 'mf'.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: soccer ranking
/*
col : name | position | league_apps | league_goals | fa_cup_apps | fa_cup_goals | league_cup_apps | league_cup_goals | total_apps | total_goals
row 1 : mike maginan | df | 0 | 0 | 0 | 0 | 0 (1) | 0 | 0 (1) | 0
row 2 : tommy chris | df | 46 | 2 | 2 | 0 | 4 | 1 | 52 | 3
row 3 : johny lowe | mf | 39 (1) | 10 | 1 | 0 | 4 | 0 | 44 (1) | 10
row 4 : hannah denver | fw | 30 (8) | 17 | 2 | 0 | 3 | 1 | 35 (8) | 18
*/
Query: none of the players scored at fa cup
Plan:
1. Select rows where 'fa_cup_goals' is not 0.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: sales records
/*
col : id | product | region | sales
row 1 : 1 | laptop | north | 100
row 2 : 2 | tablet | south | 150
row 3 : 3 | smartphone | north | 200
row 4 : 4 | laptop | south | 250
*/
Query: the total sales in the north region is 300.
Plan:
1. Select rows where 'region' is 'north'.
2. Extract the total sales in the north region by adding 'sales' column values then add column 'total_sale' to existing table.
3. Select rows where 'total_sale' is 300.
4. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: project deadlines
/*
col : id | project | department | deadline
row 1 : 1 | migration | it | 2023-12-01
row 2 : 2 | rebranding | marketing | 2023-11-15
row 3 : 3 | audit | finance | 2023-12-20
*/
Query: the audit project has the latest deadline.
Plan:
1. Order the table by 'deadline' in descending order.
2. Select row number 1.
3. Select rows where 'project' is 'audit'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: student test scores
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 8+9=17
row 2 : 2 | bob | math | 9+7=16
row 3 : 3 | charlie | math | 7+7=14
row 4 : 4 | dave | math | 7+6=13
*/
Query: the total score of charlie is 14.
Plan:
1. Extract the numerical total score from the 'score' column then add column 'num_total_score' to existing table.
2. Select rows where 'num_total_score' is 14.
3. Select rows where 'student' is 'charlie'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: project deadlines 2024
/*
col : id | project | deadline
row 1 : 1 | migration | 2024-03-01
row 2 : 2 | rebranding | 2024-12-15
row 3 : 3 | audit | 2024-05-30
*/
Query: all project deadlines are in 2024.
Plan:
1. Extract the numerical year from the 'deadline' column then add column 'year' to existing table.
2. Select rows where 'year' is not 2024.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: project deadlines 2024
/*
col : group | project | deadline
row 1 : 10 | migration | 2024-03-01
row 2 : 10 | rebranding | 2024-12-15
row 3 : 10 | audit | 2024-05-30
*/
Query: only group ten's projects were listed.
Plan:
1. Select rows where 'group' is not 10.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: project deadlines 2024
/*
col : group | project | date
row 1 : 10 | migration | 2024-03-01
row 2 : 10 | rebranding | 2024-12-15
row 3 : 10 | audit | 2024-05-30
*/
Query: migration was the project of the earliest date.
Plan:
1. Order the table by 'date' in ascending order.
2. Select row number 1.
3. Select rows where 'project' is 'migration'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: tech conference attendance
/*
col : id | conference | location | attendance
row 1 : 1 | conf A | san francisco | 32000
row 2 : 2 | conf B | new york | 34000
row 3 : 3 | conf C | chicago | 31000
*/
Query: all conferences have more than 30000 attendees.
Plan:
1. Select rows where 'attendance' is less than or equal to 30000.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: international chess tournament
/*
col : id | player | country | games_won
row 1 : 1 | alice | usa | 5
row 2 : 2 | bob | uk | 3
row 3 : 3 | charlie | india | 4
row 4 : 4 | dave | usa | 6
*/
Query: all players from usa won more than 4 games.
Plan:
1. Select rows where 'country' is 'usa'.
2. Select rows where 'games_won' is less than or equal to 4.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
/*
col : game_id | venue | date
row 1 : 1 | orlando | 2024-11-23
row 2 : 2 | new york | 2022-09-12
row 3 : 3 | san jose | 2024-09-11
*/
Query: how many games were played on different dates?
Plan:
1. Count the number of distinct dates from the 'date' column.

### Table:
/*
col : id | product | region | sales
row 1 : 1 | laptop | north | 100
row 2 : 2 | tablet | south | 150
row 3 : 3 | smartphone | north | 200
*/
Query: what are the total sales in the north region?
Plan:
1. Select rows where 'region' is 'north'.
2. Sum the sales from the 'sales' column.

### Table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 85
row 2 : 2 | bob | math | 90
row 3 : 3 | charlie | math | 80
*/
Query: what is the score of charlie in math?
Plan:
1. Select rows where 'student' is 'charlie' and 'subject' is 'math'.
2. Select the 'score' column.

### Table:
/*
col : id | product | quarter | sales
row 1 : 1 | laptop | Q1 | 100000
row 2 : 2 | tablet | Q1 | 150000
row 3 : 3 | smartphone | Q1 | 120000
*/
Query: which product had the highest sales in Q2?
Plan:
1. Select rows where 'quarter' is 'Q2'.
2. Order the table by 'sales' in descending order.
3. Select row number 1.
4. Select the 'product' column.

### Table:
/*
col : author | genre | books_sold
row 1 : smith | fiction | 300
row 2 : doe | fiction | 400
row 3 : roe | non-fiction | 500
*/
Query: which genre had the highest book sales?
Plan:
1. Order the table by 'books_sold' in descending order.
2. Select row number 1.
3. Select the 'genre' column.

### Table:
/*
col : employee | department | money_per_hour
row 1 : alice | hr | 50.55
row 2 : bob | hr | 55.75
row 3 : charlie | it | 60.33
*/
Query: who earned the most money per hour in 2018?
Plan:
1. Order the table by 'money_per_hour' in descending order.
2. Select row number 1.
3. Select the 'employee' column.

### Table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 85
row 2 : 2 | bob | math | 90
row 3 : 3 | charlie | math | 80
*/
Query: who has the third highest score in math?
Plan:
1. Order the table by 'score' in descending order.
2. Select rows where 'subject' is 'math'.
3. Select row number 3.
4. Select the 'student' column.

### Table:
/*
col : id | runner | country | time
row 1 : 1 | alice | usa | 2:45:30
row 2 : 2 | bob | kenya | 2:12:45
row 3 : 3 | charlie | uk | 2:35:10
*/
Query: who had the fastest time in the marathon?
Plan:
1. Extract the number of seconds from the 'time' column then add column 'secs' to existing table.
2. Order the table by 'secs' in ascending order.
3. Select row number 1.
4. Select the 'runner' column.

### Table:
/*
col : id | runner | country | time
row 1 : 1 | alice | usa | 2:45:30
row 2 : 2 | bob | kenya | 2:12:45
row 3 : 3 | charlie | uk | 2:35:10
*/
Query: how long does it take for bob to finish?
Plan:
1. Select rows where 'runner' is 'bob'.
2. Select the 'time' column.

### Table:
/*
col : name | position | league_apps | total_apps
row 1 : mike maginan | df | 0 | 0
row 2 : tommy chris | df | 46 | 52
row 3 : johny lowe | mf | 39 | 44
*/
Query: how many players have total apps more than 50?
Plan:
1. Select rows where 'total_apps' is greater than 50.
2. Count the number of rows.

### Table:
/*
col : id | project | department | deadline
row 1 : 1 | migration | it | 2023-12-01
row 2 : 2 | rebranding | marketing | 2023-11-15
row 3 : 3 | audit | finance | 2023-12-20
*/
Query: which project has the latest deadline?
Plan:
1. Order the table by 'deadline' in descending order.
2. Select row number 1.
3. Select the 'project' column.

### Table:
/*
col : id | project | department | deadline
row 1 : 1 | migration | it | 2023-12-01
row 2 : 2 | rebranding | marketing | 2023-11-15
row 3 : 3 | audit | finance | 2023-12-20
*/
Query: when is the dealine for rebrand?
Plan:
1. Select rows where 'project' is 'rebrand'.
2. Select the 'deadline' column.

### Table:
/*
col : id | conference | location | attendance
row 1 : 1 | conf A | san francisco | 32000
row 2 : 2 | conf B | new york | 34000
row 3 : 3 | conf C | chicago | 31000
*/
Query: how many conferences had more than 30000 attendees?
Plan:
1. Select rows where 'attendance' is greater than 30000.
2. Count the number of rows.

### Table:
/*
col : student_id | name | subject | grade | year
row 1 : 1 | alice | math | a | 2021
row 2 : 2 | bob | math | b | 2021
row 3 : 3 | charlie | science | a | 2021
*/
Query: how many students got an 'a' in math?
Plan:
1. Select rows where 'subject' is 'math' and 'grade' is 'a'.
2. Count the number of rows.

### Table:
/*
col : product_id | product_name | launch_date | units_sold
row 1 : 1 | phone x | 2021-09-01 | 10000
row 2 : 2 | laptop y | 2021-08-15 | 15000
row 3 : 3 | tablet z | 2021-07-20 | 12000
*/
Query: which product had the highest units sold?
Plan:
1. Order the table by 'units_sold' in descending order.
2. Select row number 1.
3. Select the 'product_name' column.

### Table:
/*
col : id | model | year | sales
row 1 : 1 | model a | 2021 | 50000
row 2 : 2 | model b | 2020 | 60000
row 3 : 3 | model c | 2021 | 55000
*/
Query: what is the total sales for all cars in 2021?
Plan:
1. Select rows where 'year' is 2021.
2. Sum the sales from the 'sales' column.

### Table:
/*
col : movie_id | title | genre | rating
row 1 : 1 | movie a | action | 8.5
row 2 : 2 | movie b | drama | 7.8
row 3 : 3 | movie c | comedy | 6.9
*/
Query: which movie has the lowest rating?
Plan:
1. Order the table by 'rating' in ascending order.
2. Select row number 1.
3. Select the 'title' column.

### Table:
/*
col : ranking | title | genre
row 1 : 1 | movie a | action
row 2 : 2 | movie b | drama
row 3 : 3 | movie c | comedy
*/
Query: which movies are top-2 best ranked?
Plan:
1. Order the table by 'ranking' in ascending order.
2. Select row number 1 and 2.
3. Select the 'title' column.

### Table:
/*
col : year | team | goals_scored | goals_conceded
row 1 : 2018 | france | 14 | 4
row 2 : 2014 | germany | 18 | 7
row 3 : 2010 | spain | 8 | 2
*/
Query: which team had the most goals scored in the world cup?
Plan:
1. Order the table by 'goals_scored' in descending order.
2. Select row number 1.
3. Select the 'team' column.

### Table:
/*
col : year | school | graduates | dropouts
row 1 : 2020 | school a | 200 | 20
row 2 : 2019 | school b | 180 | 25
row 3 : 2021 | school a | 220 | 15
*/
Query: which year had the highest number of graduates from school a?
Plan:
1. Select rows where 'school' is 'school a'.
2. Order the table by 'graduates' in descending order.
3. Select row number 1.
4. Select the 'year' column.

### Table:
/*
col : quarter | revenue | expenses | profit
row 1 : Q1 | 100000 | 50000 | 50000
row 2 : Q2 | 150000 | 70000 | 80000
row 3 : Q3 | 200000 | 90000 | 110000
*/
Query: which quarter had the highest profit?
Plan:
1. Order the table by 'profit' in descending order.
2. Select row number 1.
3. Select the 'quarter' column.

### Table:
/*
col : airport_code | city | passengers | flights
row 1 : jfk | new york | 300000 | 2000
row 2 : lax | los angeles | 350000 | 1800
row 3 : ord | chicago | 250000 | 2200
*/
Query: which airport had the highest number of passengers?
Plan:
1. Order the table by 'passengers' in descending order.
2. Select row number 1.
3. Select the 'airport_code' column.
"""


tabfact_natural_language_plan_demo = """
We are working on Table Fact Verification task (TabFact dataset).
Your task is to develop step-by-step plan to verify if a given Statement is TRUE or FALSE on a given Table.
There exists data where smaller values indicate better, greater, or more favorable conditions, such as rankings, times, error rates, etc.

Here are example plans you can refer to:

### Table:
table caption: 2005 tournament results
/*
col : id | name | hometown | score
row 1 : 1 | alice | new york | 85
row 2 : 2 | bob | los angeles | 90
row 3 : 3 | charlie | chicago | 75
row 4 : 4 | dave | new york | 88
row 5 : 5 | eve | los angeles | 92
*/
Statement: in 2005 tournament, bob and charlie are both from chicago.
Plan:
1. Select rows where the 'name' is 'bob' or 'charlie'.
2. Select rows where 'hometown' is 'chicago'.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

### Table:
table caption: salary last year
/*
col : id | name | department | salary | years
row 1 : 1 | alice | it | $95,000 | 3
row 2 : 2 | bob | finance | $105,000 | 5
row 3 : 3 | charlie | marketing | $88,000 | 2
*/
Statement: no employee earns more than $100,000.
Plan:
1. Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
2. Select rows where the 'num_salary' is greater than 100000.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: 2000 uk championship
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | e
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | +3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | +2
row 4 : t4 | james canpo | france | 35 + 45 = 80 | -2
*/
Statement: james canpo is the only player from france
Plan:
1. Extract the number of players from france from the 'country' column then add column 'france_cnt' to existing table.
2. Select rows where 'france_cnt' is 1.
3. Select rows where 'player' is 'james canpo'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: olympic 2018; table tennis
/*
col : rank | athlete | time
row 1 : 1 | manjeet kaur (ind) | 52.17
row 2 : 2 | olga tereshkova (kaz) | 51.86
row 3 : 3 | pinki pramanik (ind) | 53.06
*/
Statement: in table tennis of olympic 2018, there are at most 2 athletes from india.
Plan: 
1. Select rows where 'athlete' is 'ind' using LIKE function.
2. Use a `CASE` statement to return TRUE if the number of rows is smaller than or equal to 2, otherwise return FALSE.

### Table:
table caption: olympic 2018; table tennis
/*
col : rank | athlete | time
row 1 : 1 | manjeet kaur (ind) | 52.17
row 2 : 2 | olga tereshkova (kaz) | 51.86
row 3 : 3 | pinki pramanik (ind) | 53.06
*/
Statement: manjeet had the highest rank in the competition.
Plan: 
1. Order the table by 'rank' in ascending order.
2. Select row number 1.
3. Select rows where 'athlete' is 'manjeet' using LIKE function.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: book sale
/*
col : author | genre | books_sold
row 1 : smith | fiction | 300
row 2 : doe | fiction | 400
row 3 : roe | non-fiction | 500
*/
Statement: fiction is the best-selling genre.
Plan:
1. Order the table by 'books_sold' in descending order.
2. Select row number 1.
3. Select rows where 'genre' is 'fiction'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: book sale
/*
col : author | genre | books_sold
row 1 : smith | fiction | 300
row 2 : doe | fiction | 400
row 3 : roe | non-fiction | 500
*/
Statement: the maximum number of books sold is 600.
Plan:
1. Order the table by 'books_sold' in descending order.
2. Select row number 1.
3. Select rows where 'books_sold' is 600.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: us open 2024
/*
col : game | venue | date | attendance
row 1 : 1 | orlando | 2024-11-23 | 52000
row 2 : 2 | new york | 2022-09-12 | 51000
row 3 : 3 | san jose | 2024-09-09 | 53000
*/
Statement: the earliest game was played in orlando.
Plan: 
1. Order the table by 'date' in ascending order.
2. Select row number 1.
3. Select rows where 'venue' is 'orlando'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: opponents of wildcats
/*
col : game_id | venue | when | attendance | team | game
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic | away
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks | away
row 3 : 3 | orlando | 2024-09-11 | 50000 | tigers | away
*/
Statement: all matches are on different dates
Plan:
1. Extract the number of distinct dates from the 'when' column then add column 'date_cnt' to existing table.
2. Select rows where 'date_cnt' is 3.
3. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: attendance record in 2024
*/
col : game | venue | date | attendance
row 1 : 1 | orlando | 2024-11-23 | 52000
row 2 : 2 | new york | 2022-09-12 | 51000
row 3 : 3 | san jose | 2024-09-09 | 53000
*/
Statement: all the games are played in 2024
Plan: 
1. Extract the numerical year from the 'date' column then add column 'year' to existing table.
2. Select rows where 'year' is not 2024.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: attendance record in 2024
*/
col : game | venue | date | attendance
row 1 : 1 | orlando | 2024-11-23 | 52000
row 2 : 2 | new york | 2022-09-12 | 51000
row 3 : 3 | san jose | 2024-09-09 | 53000
*/
Statement: the lowest attendance was 50000
Plan: 
1. Order the table by 'attendance' in ascending order.
2. Select row number 1.
3. Select rows where 'attendance' is 50000.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: final rankings and medals
/*
col : id | athlete | country | sport | medals
row 1 : 1 | alice | usa | swimming | 5
row 2 : 2 | bob | canada | hockey | 3
row 3 : 3 | charlie | australia | athletics | 2
*/
Statement: there is no athlete from canada.
Plan:
1. Select rows where 'country' is 'canada'.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: final rankings 2009
/*
col : rank_sport | athlete | country | sport | medals
row 1 : 1 | alice | usa | swimming | 5
row 2 : 2 | bob | canada | hockey | 3
row 3 : 3 | charlie | australia | athletics | 2
row 4 : 4 | park | korea | gymnastics | 1
*/
Statement: park has the lowest sport rank in 2009.
Plan:
1. Order the table by 'rank_sport' in descending order.
2. Select row number 1.
3. Select rows where 'athlete' is 'park'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: olympic rankings
/*
col : rank | total_medals | country | silver_medals | gold_medals
row 1 : 1 | 7 | usa | 2 | 5
row 2 : 2 | 7 | canada | 4 | 3
row 3 : 3 | 4 | australia | 2 | 2
*/
Statement: canada has the highest number of silver medals.
Plan:
1. Order the table by 'silver_medals' in descending order.
2. Select row number 1.
3. Select rows where 'country' is 'canada'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: game results in 2024
/*
col : game_id | venue | date | attendance | team
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks
row 3 : 3 | san jose | 2024-09-09 | 35000 | sharks
*/
Statement: no games were played in december.
Plan:
1. Extract the numerical month from the 'date' column then add column 'month' to existing table.
2. Select rows where 'month' is 12.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: list of winners
/*
col : id | player | country | sport | medals
row 1 : 1 | alice | usa | swimming | 5
row 2 : 2 | bob | canada | hockey | 3
row 3 : 3 | charlie | italia | athletics | 2
*/
Statement: there are less than 2 players from italia in the list of winners.
Plan:
1. Select rows where 'country' is 'italia'.
2. Use a `CASE` statement to return TRUE if the number of rows is smaller than 2, otherwise return FALSE.

### Table:
table caption: opponents of wildcats
/*
col : game_id | venue | date | attendance | team
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks
row 3 : 3 | san jose | 2024-09-09 | 35000 | sharks
*/
Statement: sharks was the opponent of the last game.
Plan:
1. Order the table by 'game_id' in descending order.
2. Select row number 1.
3. Select rows where 'team' is 'sharks'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: book sales
/*
col : iso/iec_standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2011) | 7
*/
Statement: 2 standards are published in 2011.
Plan: 
1. Extract the year from the 'status' column then add column 'year_published' to existing table.
2. Select rows where 'year_published' is 2011.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

### Table:
table caption: book sales
/*
col : iso/iec_standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2011) | 7
*/
Statement: the standard tr 19759 was released in 2005.
Plan: 
1. Extract the year from the 'status' column then add column 'year_published' to existing table.
2. Select rows where 'year_published' is 2005.
3. Select rows where 'iso/iec_standard' is 'tr 19759'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: 2018 financial report
/*
col : employee | department | money_per_hour
row 1 : alice | hr | 50.55
row 2 : bob | hr | 55.75
row 3 : charlie | it | 60.33
*/
Statement: in 2018, alice earned the most money per hour.
Plan: 
1. Order the table by 'money_per_hour' in descending order.
2. Select row number 1.
3. Select rows where the 'employee' is 'alice'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: project list
/*
col : project_id | project_name | department | start_date | deadline
row 1 : 1 | migration | it | 2023-01-15 | 2024-03-01
row 2 : 2 | rebranding | marketing | 2023-06-20 | 2023-12-15
row 3 : 3 | audit | finance | 2023-09-10 | 2024-05-30
*/
Statement: no project deadline is set before 2024.
Plan:
1. Extract the numerical year from the 'deadline' column then add column 'year' to existing table.
2. Select rows where the 'year' is before 2024.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 80
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/
Statement: the average score of all employees is above 85.
Plan:
1. Extract the average of the 'score' column then add column 'avg_score' to existing table.
2. Select rows where the 'avg_score' is greater than 85.
3. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 80
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/
Statement: eve had the most score among the listed players.
Plan:
1. Order the table by 'score' in descending order.
2. Select row number 1.
3. Select rows where the 'name' is 'eve'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 70
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 85
row 5 : 5 | eve | hr | 95
*/
Statement: the difference between the highest and lowest scores is more than 20.
Plan:
1. Extract the difference between the maximum value and minimum value of the 'score' column then add column 'score_diff' to existing table.
2. Select rows where the 'score_diff' is greater than 20.
3. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: team building in nyc
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 70
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/
Statement: dave and bob together had the least amount of scores.
Plan:
1. Extract the minimum value of the 'score' column then add column 'min_score' to existing table.
2. Select rows where the 'score' is equal to 'min_score'.
3. Select rows where 'name' is 'dave' or 'bob'
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

### Table:
table caption: opponents of wildcats
/*
col : game_id | venue | date | attendance | team | game
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic | away
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks | away
row 3 : 3 | orlando | 2024-09-11 | 50000 | tigers | away
*/
Statement: attendance of games in orlando is always over 50000.
Plan:
1. Select rows where 'venue' is 'orlando'.
2. Select rows where the 'attendance' is less than or equal to 50000.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: soccer ranking
/*
col : name | position | league_apps | league_goals | fa_cup_apps | fa_cup_goals | league_cup_apps | league_cup_goals | total_apps | total_goals
row 1 : mike maginan | df | 0 | 0 | 0 | 0 | 0 (1) | 0 | 0 (1) | 0
row 2 : tommy chris | df | 46 | 2 | 2 | 0 | 4 | 1 | 52 | 3
row 3 : johny lowe | mf | 39 (1) | 10 | 1 | 0 | 4 | 0 | 44 (1) | 10
row 4 : hannah denver | fw | 30 (8) | 17 | 2 | 0 | 3 | 1 | 35 (8) | 18
*/
Statement: tommy chris played at mf
Plan:
1. Select rows where 'name' is 'tommy chris'.
2. Select rows where 'position' is 'mf'.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: soccer ranking
/*
col : name | position | league_apps | league_goals | fa_cup_apps | fa_cup_goals | league_cup_apps | league_cup_goals | total_apps | total_goals
row 1 : mike maginan | df | 0 | 0 | 0 | 0 | 0 (1) | 0 | 0 (1) | 0
row 2 : tommy chris | df | 46 | 2 | 2 | 0 | 4 | 1 | 52 | 3
row 3 : johny lowe | mf | 39 (1) | 10 | 1 | 0 | 4 | 0 | 44 (1) | 10
row 4 : hannah denver | fw | 30 (8) | 17 | 2 | 0 | 3 | 1 | 35 (8) | 18
*/
Statement: none of the players scored at fa cup
Plan:
1. Select rows where 'fa_cup_goals' is not 0.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: sales records
/*
col : id | product | region | sales
row 1 : 1 | laptop | north | 100
row 2 : 2 | tablet | south | 150
row 3 : 3 | smartphone | north | 200
row 4 : 4 | laptop | south | 250
*/
Statement: the total sales in the north region is 300.
Plan:
1. Select rows where 'region' is 'north'.
2. Extract the total sales in the north region by adding 'sales' column values then add column 'total_sale' to existing table.
3. Select rows where 'total_sale' is 300.
4. Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

### Table:
table caption: project deadlines
/*
col : id | project | department | deadline
row 1 : 1 | migration | it | 2023-12-01
row 2 : 2 | rebranding | marketing | 2023-11-15
row 3 : 3 | audit | finance | 2023-12-20
*/
Statement: the audit project has the latest deadline.
Plan:
1. Order the table by 'deadline' in descending order.
2. Select row number 1.
3. Select rows where 'project' is 'audit'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: student test scores
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 8+9=17
row 2 : 2 | bob | math | 9+7=16
row 3 : 3 | charlie | math | 7+7=14
row 4 : 4 | dave | math | 7+6=13
*/
Statement: the total score of charlie is 14.
Plan:
1. Extract the numerical total score from the 'score' column then add column 'num_total_score' to existing table.
2. Select rows where 'num_total_score' is 14.
3. Select rows where 'student' is 'charlie'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: project deadlines 2024
/*
col : id | project | deadline
row 1 : 1 | migration | 2024-03-01
row 2 : 2 | rebranding | 2024-12-15
row 3 : 3 | audit | 2024-05-30
*/
Statement: all project deadlines are in 2024.
Plan:
1. Extract the numerical year from the 'deadline' column then add column 'year' to existing table.
2. Select rows where 'year' is not 2024.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: project deadlines 2024
/*
col : group | project | deadline
row 1 : 10 | migration | 2024-03-01
row 2 : 10 | rebranding | 2024-12-15
row 3 : 10 | audit | 2024-05-30
*/
Statement: only group ten's projects were listed.
Plan:
1. Select rows where 'group' is not 10.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: project deadlines 2024
/*
col : group | project | date
row 1 : 10 | migration | 2024-03-01
row 2 : 10 | rebranding | 2024-12-15
row 3 : 10 | audit | 2024-05-30
*/
Statement: migration was the project of the earliest date.
Plan:
1. Order the table by 'date' in ascending order.
2. Select row number 1.
3. Select rows where 'project' is 'migration'.
4. Use a `CASE` statement to return TRUE if the number of rows is equal to 1, otherwise return FALSE.

### Table:
table caption: tech conference attendance
/*
col : id | conference | location | attendance
row 1 : 1 | conf A | san francisco | 32000
row 2 : 2 | conf B | new york | 34000
row 3 : 3 | conf C | chicago | 31000
*/
Statement: all conferences have more than 30000 attendees.
Plan:
1. Select rows where 'attendance' is less than or equal to 30000.
2. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

### Table:
table caption: international chess tournament
/*
col : id | player | country | games_won
row 1 : 1 | alice | usa | 5
row 2 : 2 | bob | uk | 3
row 3 : 3 | charlie | india | 4
row 4 : 4 | dave | usa | 6
*/
Statement: all players from usa won more than 4 games.
Plan:
1. Select rows where 'country' is 'usa'.
2. Select rows where 'games_won' is less than or equal to 4.
3. Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.
"""


#####################################################################################################################################
tabfact_natural_language_step_to_sql_demo = """
We are working on the task of converting natural language action into SQL command.

###
Given this table:
/*
col : competition | date | location | attendance
row 1 : conference 1 | 2024-06-01 | new york | 32092
row 2 : conference 2 | 2024-06-15 | san francisco | 34186
row 3 : conference 3 | 2024-07-20 | chicago | 17503
*/

Write a SQL command that: Extract the 'year' from the 'date' column then add column 'year' to existing table.

SQL is:
```sql
SELECT *,
       STRFTIME('%Y', date) AS year
FROM table_sql;
--  Extract the 'year' from the 'date' column then add column 'year' to existing table.
```

###
Given this table:
/*
col : id | name | department | salary | years
row 1 : 1 | alice | it | $95,000 | 3
row 2 : 2 | bob | finance | $105,000 | 5
row 3 : 3 | charlie | marketing | $88,000 | 2
*/

Write a SQL command that: Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.

SQL is:
```sql
SELECT *,
    CAST(REPLACE(REPLACE(salary, '$', ''), ',', '') AS INTEGER) AS num_salary
FROM table_sql;
-- Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
```

###
Given this table:
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | e
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | +3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | +2
row 4 : t4 | james canpo | france | 35 + 45 = 80 | -2
*/

Write a SQL command that: Extract the number of players from france from the 'country' column then add column 'france_cnt' to existing table

SQL is:
```sql
SELECT *,
       (SELECT COUNT(*) FROM table_sql WHERE country LIKE '%france%') AS france_cnt
FROM table_sql;
-- Extract the number of players from france from the 'country' column then add column 'france_cnt' to existing table
```

###
Given this table:
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | e
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | +3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | +2
row 4 : t4 | james canpo | france | 35 + 45 = 80 | -2
*/

Write a SQL command that: Select rows where 'score' is '68 + 68'

SQL is:
```sql
SELECT *
FROM table_sql
WHERE score LIKE '%68 + 68%';
-- Select rows where 'score' is '68 + 68'
```

###
Given this table:
/*
col : rank | player | games | scores
row 1 : 1 | alex smith | 45 | 23.4(11)
row 2 : 2 | john doe | 43 | 14.2(8)
row 3 : 3 | jane doe | 32 | 9.6(6)
row 4 : 4 | emily johnson | 17 | 3.2(3)
*/

Write a SQL command that: Select rows where 'player' is not 'jane doe'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE player != 'jane doe';
-- Select rows where 'player' is not 'jane doe'.
```

###
Given this table:
/*
col : rank | player | games | scores
row 1 : 1 | alex smith | 45 | 23.4(11)
row 2 : 2 | john doe | 43 | 14.2(8)
row 3 : 3 | jane doe | 32 | 9.6(6)
row 4 : 4 | emily johnson | 17 | 3.2(3)
*/

Write a SQL command that: Select rows where 'games' is not 16.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE games != 16;
-- Select rows where 'games' is not 16.
```

###
Given this table:
/*
col : id | name | department | salary | years
row 1 : 1 | alice | it | 95000 | 3
row 2 : 2 | bob | finance | 105000 | 5
row 3 : 3 | charlie | marketing | 88000 | 2
*/

Write a SQL command that: Select rows where the 'salary' is greater than 100000.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE salary > 100000;
-- Select rows where the 'salary' is greater than 100000.
```

###
Given this table:
/*
col : when | competition | venue | position | notes
row 1 : 2014-01-01 | city marathon | new york, usa | 2nd | 2:30:45
row 2 : 2015-01-01 | international marathon | london, uk | 1st | 2:25:30
row 3 : 2017-01-01 | national marathon | berlin, germany | 5th | 2:35:10
row 4 : 2020-01-01 | city marathon | tokyo, japan | 3rd | 2:28:40
row 5 : 2022-01-01 | olympic games | paris, france | 4th | 2:32:00
*/

Write a SQL command that: Select rows where 'competition' is 'marathon'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE competition LIKE '%marathon%';
-- Select rows where 'competition' is 'marathon'.
```

###
Given this table:
/*
col : id | name | hometown | score
row 1 : 1 | alice | new york | 85
row 2 : 2 | bob | los angeles | 90
row 3 : 3 | charlie | chicago | 75
row 4 : 4 | dave | new york | 88
row 5 : 5 | eve | los angeles | 92
*/

Write a SQL command that: Select rows where the 'name' is 'bob' or 'charlie'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE name LIKE '%bob%' OR name LIKE '%charlie%';
-- Select rows where the 'name' is 'bob' or 'charlie'.
```

###
Given this table:
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 80
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/

Write a SQL command that: Extract the average of the 'score' column then add column 'avg_score' to existing table.

SQL is:
```sql
SELECT *, 
    (SELECT AVG(score) FROM table_sql) AS avg_score
FROM table_sql;
-- Extract the average of the 'score' column then add column 'avg_score' to existing table.
```

###
Given this table:
/*
col : id | runner | country | time
row 1 : 1 | alice | usa | 2:45:30
row 2 : 2 | bob | kenya | 2:12:45
row 3 : 3 | charlie | uk | 2:35:10
*/

Write a SQL command that: Extract the number of seconds from the 'time' column then add column 'secs' to existing table.

SQL is:
```sql
SELECT *,
       CAST(SUBSTR(time, 1, 2) AS INTEGER) * 3600 + 
       CAST(SUBSTR(time, 4, 2) AS INTEGER) * 60 + 
       CAST(SUBSTR(time, 7, 2) AS INTEGER) AS secs
FROM table_sql;
-- Extract the number of seconds from the 'time' column then add column 'secs' to existing table.
```

###
Given this table:
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 80
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/

Write a SQL command that: Extract the difference between the maximum value and minimum value of the 'score' column then add column 'score_diff' to existing table.

SQL is:
```sql
SELECT *, (SELECT MAX(score) - MIN(score) FROM table_sql) AS score_diff
FROM table_sql;
-- Extract the difference between the maximum value and minimum value of the 'score' column then add column 'score_diff' to existing table.
```

###
Given this table:
/*
col : game | winner | result
row 1 : 1 | alex smith | 45-23
row 2 : 2 | john doe | 43-14
row 3 : 3 | jane doe | 32-9
row 4 : 4 | emily johnson | 17-23
*/

Write a SQL command that: Extract the numerical total score from the 'result' column by adding the two numbers then add column 'total_score' to existing table.

SQL is:
```sql
SELECT *,
       CAST(SUBSTR(result, 1, INSTR(result, '-') - 1) AS INTEGER) + 
       CAST(SUBSTR(result, INSTR(result, '-') + 1) AS INTEGER) AS total_score
FROM table_sql;
-- Extract the numerical total score from the 'result' column by adding the two numbers then add column 'total_score' to existing table.
```

###
Given this table:
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | e
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | +3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | +2
row 4 : t4 | james canpo | france | 35 + 45 = 80 | -2
*/
Write a SQL command that: Select rows where 'country' is 'france' or 'player' is 'james canpo'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE country LIKE '%france%' OR player LIKE '%james canpo%';
-- Select rows where 'country' is 'france' or 'player' is 'james canpo'.
```

###
Given this table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 90
row 2 : 2 | bob | math | 80
row 3 : 3 | charlie | math | 80
row 4 : 4 | dave | math | 75
*/

Write a SQL command that: Select row number 1.

SQL is:
```sql
SELECT *
FROM table_sql
LIMIT 1;
-- Select row number 1.
```

###
Given this table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 90
row 2 : 2 | bob | math | 80
row 3 : 3 | charlie | math | 80
row 4 : 4 | dave | math | 75
*/

Write a SQL command that: Select row number 2.

SQL is:
```sql
SELECT *
FROM table_sql
LIMIT 1 OFFSET 1;
-- Select row number 2.
```

###
Given this table:
/*
col : ranking | title | genre
row 1 : 1 | movie a | action
row 2 : 2 | movie b | drama
row 3 : 3 | movie c | comedy
*/

Write a SQL command that: Select row number 1 and 2.

SQL is:
```sql
SELECT * 
FROM table_sql
LIMIT 2;
-- Select row number 1 and 2.
```

###
Given this table:
/*
col : id | name | hometown | score
row 1 : 1 | alice | new york | 85
row 2 : 2 | bob | los angeles | 90
row 3 : 3 | charlie | chicago | 75
row 4 : 4 | dave | new york | 88
row 5 : 5 | eve | los angeles | 92
*/

Write a SQL command that: Order the table by 'score' in descending order.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY score DESC;
-- Order the table by 'score' in descending order.
```

###
Given this table:
/*
col : competition | date | location | attendance
row 1 : conference 1 | 2024-06-01 | new york | 3.21
row 2 : conference 2 | 2024-06-15 | san francisco | 3.41
row 3 : conference 3 | 2024-07-20 | chicago | 1.75
*/

Write a SQL command that: Order the table by 'attendance' in descending order.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY CAST(attendance AS REAL) DESC;
-- Order the table by 'attendance' in descending order.
```

###
Given this table:
/*
col : rank | player | games | scores
row 1 : 1 | alex smith | 112 | 1100
row 2 : 2 | john doe | 107 | 1050
row 3 : 3 | jane doe | 131 | 980
row 4 : 4 | emily johnson | 116 | 20
*/

Write a SQL command that: Select rows where 'rank' is greater than 2.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE rank > 2;
-- Select rows where 'rank' is greater than 2.
```

###
Given this table:
/*
col : id | name | department | score | min_score
row 1 : 1 | alice | hr | 90 | 70
row 2 : 2 | bob | it | 70 | 70
row 3 : 3 | charlie | finance | 88 | 70
row 4 : 4 | dave | marketing | 70 | 70
row 5 : 5 | eve | hr | 95 | 70
*/

Write a SQL command that: Select rows where the 'score' is equal to 'min_score'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE score = min_score;
-- Select rows where the 'score' is equal to 'min_score'.
```

###
Given this table:
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | -4
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | -3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | -2
*/

Write a SQL command that: Extract numerical score value from 'score' column then add a column 'num_score' to existing table.

SQL is:
```sql
SELECT *,
       CAST(SUBSTR(score, INSTR(score, '=') + 2) AS INT) AS num_score
FROM table_sql;
-- Extract numerical score value from 'score' column then add a column 'num_score' to existing table.
```

###
Given this table:
/*
col : player | hometown
row 1 : andy helpmin | washington , la
row 2 : tommy lennon        | birmingham , al
*/

Write a SQL command that: Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

SQL is:
```sql
SELECT CASE 
         WHEN COUNT(*) = 2 THEN 'TRUE'
         ELSE 'FALSE'
       END AS verification_result
FROM table_sql;
-- Returns 'TRUE' if there exists 2 rows, otherwise return 'FALSE'.
```

###
Given this table:
/*
col : game | venue | result | date
row 1 : 1 | nyc | 45-23 | 2024-11-23
row 2 : 2 | syd | 43-14 | 2024-11-21
row 3 : 3 | ark | 32-9 | 2024-11-20
row 4 : 4 | atl | 17-23 | 2024-11-14
*/

Write a SQL command that: Extract the win/loss from the 'result' column then add column 'win_loss' to existing table.

SQL is:
```sql
SELECT *,
       CASE
           WHEN CAST(SUBSTR(result, 1, INSTR(result, '-') - 1) AS INT) > CAST(SUBSTR(result, INSTR(result, '-') + 1) AS INT) THEN 'w'
           ELSE 'l'
       END AS win_loss
FROM table_sql;
-- Extract the win/loss from the 'result' column then add column 'win_loss' to existing table.
```

###
Given this table:
/*
col : point_difference
row 1 : 150
*/

Write a SQL command that: Use a `CASE` statement to return TRUE if the number of rows is greater than or equal to 1, otherwise return FALSE.

SQL is:
```sql
SELECT CASE 
         WHEN COUNT(*) >= 1 THEN 'TRUE'
         ELSE 'FALSE'
       END AS verification_result
FROM table_sql;
-- Returns 'TRUE' if there exists greater than or equal to one row, otherwise return 'FALSE'.
```

###
Given this table:
/*
col : game_date
row 1 : june 20
*/

Write a SQL command that: Use a `CASE` statement to return TRUE if the number of rows is equal to 0, otherwise return FALSE.

SQL is:
```sql
SELECT CASE 
         WHEN COUNT(*) = 0 THEN 'TRUE'
         ELSE 'FALSE'
       END AS verification_result
FROM table_sql;
-- Returns 'TRUE' if there exists no row, otherwise return 'FALSE'.
```

###
Given this table:
/*
col : id | player | country | sport | medals
row 1 : 3 | charlie | italia | athletics | 2
*/

Write a SQL command that: Use a `CASE` statement to return TRUE if the number of rows is smaller than 2, otherwise return FALSE.

SQL is:
```sql
SELECT CASE 
         WHEN COUNT(*) < 2 THEN 'TRUE'
         ELSE 'FALSE'
       END AS verification_result
FROM table_sql;
-- Returns 'TRUE' if there exists less than 2 rows, otherwise return 'FALSE'.
```

###
Given this table:
/*
col : name | age
row 1 : alice | 30
row 2 : bob | 25
row 3 : carol | 27
row 4 : dave | 22
*/

Write a SQL command that: Use a `CASE` statement to return TRUE if the number of rows is greater than 3, otherwise return FALSE.

SQL is:
```sql
SELECT CASE 
         WHEN COUNT(*) > 3 THEN 'TRUE'
         ELSE 'FALSE'
       END AS verification_result
FROM table_sql;
-- Returns 'TRUE' if there are more than 3 rows, otherwise 'FALSE'.
```

###
Given this table:
/*
col : product | price
row 1 : apple | 1.00
row 2 : orange | 1.50
row 3 : banana | 0.75
row 4 : kiwi | 2.00
*/

Write a SQL command that: Use a `CASE` statement to return TRUE if the number of rows is equal to 2, otherwise return FALSE.

SQL is:
```sql
SELECT CASE 
         WHEN COUNT(*) = 2 THEN 'TRUE'
         ELSE 'FALSE'
       END AS verification_result
FROM table_sql;
-- Returns 'TRUE' if there are 2 rows, otherwise 'FALSE'.
```

###
Given this table:
/*
col : score
row 1 : 85
row 2 : 90
*/

Write a SQL command that: Use a `CASE` statement to return TRUE if the number of rows is smaller than or equal to 2, otherwise return FALSE.

SQL is:
```sql
SELECT CASE 
         WHEN COUNT(*) <= 2 THEN 'TRUE'
         ELSE 'FALSE'
       END AS verification_result
FROM table_sql;
-- Returns 'TRUE' if there are 2 or fewer rows, otherwise 'FALSE'.
```
"""


###############################################################################################################
###############################################################################################################
###############################################################################################################


# CHAIN-OF-TABLE demos
# Dynamic Chain Func

plan_add_column_demo = """If the table does not have the needed column to tell whether the statement is True or False, we use f_add_column() to add a new column for it. For example,
/*
col : rank | lane | player | time
row 1 : 1 | 5 | olga tereshkova (kaz) | 51.86
row 2 : 2 | 6 | manjeet kaur (ind) | 52.17
row 3 : 3 | 3 | asami tanno (jpn) | 53.04
*/
Statement: there are one athlete from japan.
Function: f_add_column(country of athlete)
Explanation: The statement is about the number of athletes from japan. We need to known the country of each athlete. There is no column of the country of athletes. We add a column "country of athlete"."""

plan_add_column_demo_sql = """If the table does not have the needed column to tell whether the statement is True or False, we add a new column for it. For example,
/*
col : rank | lane | player | time
row 1 : 1 | 5 | olga tereshkova (kaz) | 51.86
row 2 : 2 | 6 | manjeet kaur (ind) | 52.17
row 3 : 3 | 3 | asami tanno (jpn) | 53.04
*/
Statement: there are one athlete from japan.
The existing columns are: rank, lane, player, time.
SQL is: 

```sql
SELECT *,
       substr(player, instr(player, '(') + 1, instr(player, ')') - instr(player, '(') - 1) AS country_of_athletes
FROM athletes;
-- This SQL query extracts the substring between parentheses in the 'player' column to create a new column 'country_of_athletes'.
```

Explanation: To tell this statement is true or false, we need to know the country of each athlete. We extract the value from column "player" and create a different column "country of athletes" for each row. The datatype is string.
The value: kaz | ind | jpn
"""


plan_select_column_demo = """If the table only needs a few columns to tell whether the statement is True or False, we use f_select_column() to select these columns for it. For example,
/*
col : code | county | former province | area (km2) | population | capital
row 1 : 1 | mombasa | coast | 212.5 | 939,370 | mombasa (city)
row 2 : 2 | kwale | coast | 8,270.3 | 649,931 | kwale
row 3 : 3 | kilifi | coast | 12,245.9 | 1,109,735 | kilifi
*/
Statement: momasa is a county with population higher than 500000.
Function: f_select_column(county, population)
Explanation: The statement wants to check momasa county with population higher than 500000. We need to know the county and its population. We select the column "county" and column "population"."""

plan_select_column_demo_sql = """
/*
table caption: south wales derby
col: competition | total matches | cardiff win | draw | swansea win
row 1: league | 55 | 19 | 16 | 20
row 2: fa cup | 2 | 0 | 27 | 2
row 3: league cup | 5 | 2 | 0 | 3
*/
Statement: There are no cardiff wins that have a draw greater than 27.
The existing columns are: rank, lane, player, time.

SQL is:
```sql
SELECT "cardiff win", "draw"
FROM south_wales_derby;
-- This SQL query selects only the 'cardiff win' and 'draw' columns.
```

Explanation: This SQL selects two columns "cardiff win" and "draw" that are relevant to the statement.
"""

plan_select_row_demo = """If the table only needs a few rows to tell whether the statement is True or False, we use f_select_row() to select these rows for it. For example,
/*
table caption : jeep grand cherokee.
col : years | displacement | engine | power | torque
row 1 : 1999 - 2004 | 4.0l (242cid) | power tech i6 | - | 3000 rpm
row 2 : 1999 - 2004 | 4.7l (287cid) | powertech v8 | - | 3200 rpm
row 3 : 2002 - 2004 | 4.7l (287cid) | high output powertech v8 | - | -
row 4 : 1999 - 2001 | 3.1l diesel | 531 ohv diesel i5 | - | -
row 5 : 2002 - 2004 | 2.7l diesel | om647 diesel i5 | - | -
*/
Statement: the jeep grand cherokee with the om647 diesel i5 had the third lowest numbered displacement.
Function: f_select_row(row 1, row 4, row 5)
Explanation: The statement wants to check the om647 diesel i5 had third lowest numbered displacement. We need to know the first three low numbered displacement and all rows that power is om647 diesel i5. We select the row 1, row 4, row 5."""


plan_select_row_demo_sql = """If the table only needs a few rows to tell whether the statement is True or False, we select these rows for it. For example,
/*
table caption: Jeep Grand Cherokee.
col: years | displacement | engine | power | torque
row 1: 1999 - 2004 | 4.0l (242cid) | Power Tech I6 | - | 3000 rpm
row 2: 1999 - 2004 | 4.7l (287cid) | PowerTech V8 | - | 3200 rpm
row 3: 2002 - 2004 | 4.7l (287cid) | High Output PowerTech V8 | - | -
row 4: 1999 - 2001 | 3.1l diesel | 531 OHV Diesel I5 | - | -
row 5: 2002 - 2004 | 2.7l diesel | OM647 Diesel I5 | - | -
*/
Statement: The Jeep Grand Cherokee with the OM647 Diesel I5 had the third lowest numbered displacement.
SQL is:
```sql
SELECT *
FROM jeep_grand_cherokee
ORDER BY CAST(SUBSTR(displacement, 1, INSTR(displacement, 'l') - 1) AS FLOAT)
LIMIT 3;
-- This SQL query selects the three rows with the lowest displacements from the 'jeep_grand_cherokee' table.
```sql

Explanation: This SQL setup is designed to verify if the Jeep model with the OM647 Diesel I5 engine ranks among the models with the three lowest displacements, providing the necessary context for the statement's accuracy.
"""

plan_group_column_demo = """If the statement is about items with the same value and the number of these items, we use f_group_column() to group the items. For example,
/*
col : district | name | party | residence | first served
row 1 : district 1 | nelson albano | dem | vineland | 2006
row 2 : district 1 | robert andrzejczak | dem | middle twp. | 2013†
row 3 : district 2 | john f. amodeo | rep | margate | 2008
*/
Statement: there are 5 districts are democratic
Function: f_group_column(party)
Explanation: The statement wants to check 5 districts are democratic. We need to know the number of dem in the table. We group the rows according to column "party"."""

plan_group_column_demo_sql = """
If the statement is about items with the same value and the number of these items, we group the items. For example,
/*
col : district | name | party | residence | first served
row 1 : district 1 | nelson albano | dem | vineland | 2006
row 2 : district 1 | robert andrzejczak | dem | middle twp. | 2013†
row 3 : district 2 | john f. amodeo | rep | margate | 2008
row 4 : district 2 | chris a. brown | rep | ventnor | 2012
row 5 : district 3 | john j. burzichelli | dem | paulsboro | 2002
*/
Statement: the number of districts that are democratic is 5.
The existing columns are: district, name, party, residence, first served.

SQL is:

```sql
SELECT party, COUNT(*) AS num_districts
FROM government_officials
GROUP BY party;
-- Group districts by political party and count them
```

Explanation: the statement says the number of districts that are democratic is 5. Each row is about a district. We can group the column "party" to group the districts from the same party.
"""

plan_sort_column_demo = """If the statement is about the order of items in a column, we use f_sort_column() to sort the items. For example,
/*
col : position | club | played | points
row 1 : 1 | malaga cf | 42 | 79
row 10 : 10 | cp merida | 42 | 59
row 3 : 3 | cd numancia | 42 | 73
*/
Statement: cd numancia placed in the last position.
Function: f_sort_column(position)
Explanation: The statement wants to check about cd numancia in the last position. We need to know the order of position from last to front. We sort the rows according to column "position"."""

plan_sort_column_demo_sql = """If the statement is about the order of items in a column, we use sort function to sort the items. For example,
/*
col : position | club | played | points | wins | draws | losses | goals for | goals against | goal difference
row 1 : 1 | Malaga CF | 42 | 79 | 22 | 13 | 7 | 72 | 47 | +25
row 10 : 10 | CP Merida | 42 | 59 | 15 | 14 | 13 | 48 | 41 | +7
row 3 : 3 | CD Numancia | 42 | 73 | 21 | 10 | 11 | 68 | 40 | +28
*/
Statement: CD Numancia placed in the last position.
The existing columns are: position, club, played, points, wins, draws, losses, goals for, goals against, goal difference.

SQL is:

```sql
SELECT *
FROM football_league
ORDER BY position DESC;
LIMIT 1;
-- This SQL query sorts the 'position' column in descending order, to easily see the team in the last position.
```

Explanation: To verify if CD Numancia is in the last position, we sort the 'position' column from largest to smallest. 
The last row in this order will show the team in the last position.
"""

USING_SQL = False

if USING_SQL is True:
    plan_full_demo_simple = """
Here are examples of using the operations to tell whether the statement is True or False.
*/
col : rank | lane | athlete | time
row 1 : 1 | 6 | manjeet kaur (ind) | 52.17
row 2 : 2 | 5 | olga tereshkova (kaz) | 51.86
row 3 : 3 | 4 | pinki pramanik (ind) | 53.06
*/
Statement: There are 10 athletes from India.
Function Chain: f_add_column(country_athletes) -> f_select_column(country_athletes) -> f_group_column(country_athletes) -> <END>

*/
col : game | venue | date | attendance
row 1 : 1 | orlando | 2024-11-23 | 52000
row 2 : 2 | new york | 2022-09-12 | 51000
row 3 : 3 | san jose | 2024-09-09 | 53000
*/
Statement: the earliest game was played in orlando
Function Chain: f_sort_column(date) -> <END>

/*
col : week | when | kickoff | opponent | results; final score | results; team record | game site | attendance
row 1 : 1 | saturday, april 13 | 7:00 p.m. | at rhein fire | w; 27–21 | 1–0 | rheinstadion | 32,092
row 2 : 2 | saturday, april 20 | 7:00 p.m. | london monarchs | w; 37–3 | 2–0 | waldstadion | 34,186
row 3 : 3 | sunday, april 28 | 6:00 p.m. | at barcelona dragons | w; 33–29 | 3–0 | estadi | 17,503
*/
Statement: the competition with highest points scored is played on April 20.
Function Chain: f_add_column(points_scored) -> f_sort_column(points_scored) -> <END>

/*
col : iso/iec standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2011) | 7
*/
Statement: 2 standards are published in 2011
Function Chain: f_add_column(year) -> <END>

/*
col : product | store | sales
row 1 : Bread | Store A | 100
row 2 : Milk | Store B | 150
row 3 : Bread | Store C | 200
*/
Statement: Bread is sold in at least two different stores.
Function Chain: f_select_row(row 1, row 3) -> f_group_column(store) -> <END>

/*
col : name | department | salary
row 1 : Alice | HR | $50000
row 2 : Bob | HR | $55000
row 3 : Charlie | IT | $60000
*/
Statement: The highest salary in HR exceeds $52000.
Function Chain: f_add_column(num_salary) -> f_sort_column(num_salary) -> <END>

/*
col : author | genre | books_sold
row 1 : Smith | Fiction | 300
row 2 : Doe | Fiction | 400
row 3 : Roe | Non-fiction | 500
*/
Statement: Fiction is the best-selling genre.
Function Chain: f_sort_column(books_sold) -> <END>

/*
col : city | population | country
row 1 : New York | 8,000,000 | USA
row 2 : London | 9,000,000 | UK
row 3 : Tokyo | 14,000,000 | Japan
*/
Statement: New York is not the most populous city listed.
Function Chain: f_add_column(num_population) -> f_sort_column(num_population) -> <END>

/*
col : player_name | team | points | game_date
row 1 : John Doe | Rockets | 30 | 2021-06-01
row 2 : Jane Smith | Rockets | 25 | 2021-06-15
row 3 : Alice Johnson | Jets | 20 | 2021-06-02
*/
Statement: The highest point total was scored by a Rockets player.
Function Chain: f_select_column(team, points) -> f_sort_column(points) -> <END>

/*
col : product | units_sold
row 1 : Coffee | 120
row 2 : Tea | 150
row 3 : Sandwich | 200
*/
Statement: Sandwiches are the best-selling product.
Function Chain: f_sort_column(units_sold) -> <END>

*/
col : september_game
row 1 : 3
*/
Statement: spurs lost 3 games in september.
Function Chain: <END>

/*
col : date | count
row 1 : 2022-07-01 | 1
row 2 : 2022-06-09 | 2
*/
Statement: There were three games finished in 2022.
Function Chain: <END>
"""
else:
    plan_full_demo_simple = """Here are examples of using the operations to tell whether the statement is True or False.
/*
col : date | division | league | regular season | playoffs | open cup | avg. attendance
row 1 : 2001/01/02 | 2 | usl a-league | 4th, western | quarterfinals | did not qualify | 7,169
row 2 : 2002/08/06 | 2 | usl a-league | 2nd, pacific | 1st round | did not qualify | 6,260
row 5 : 2005/03/24 | 2 | usl first division | 5th | quarterfinals | 4th round | 6,028
*/
Statement: 2005 is the last year where this team was a part of the usl a-league?
Function Chain: f_add_column(year) -> f_select_row(row 1, row 2) -> f_select_column(year, league) -> f_sort_column(year) -> <END>

*/
col : rank | lane | athlete | time
row 1 : 1 | 6 | manjeet kaur (ind) | 52.17
row 2 : 2 | 5 | olga tereshkova (kaz) | 51.86
row 3 : 3 | 4 | pinki pramanik (ind) | 53.06
*/
Statement: There are 10 athletes from India.
Function Chain: f_add_column(country of athletes) -> f_select_row(row 1, row 3) -> f_select_column(athlete, country of athletes) -> f_group_column(country of athletes) -> <END>

/*
col : week | when | kickoff | opponent | results; final score | results; team record | game site | attendance
row 1 : 1 | saturday, april 13 | 7:00 p.m. | at rhein fire | w 27–21 | 1–0 | rheinstadion | 32,092
row 2 : 2 | saturday, april 20 | 7:00 p.m. | london monarchs | w 37–3 | 2–0 | waldstadion | 34,186
row 3 : 3 | sunday, april 28 | 6:00 p.m. | at barcelona dragons | w 33–29 | 3–0 | estadi olímpic de montjuïc | 17,503
*/
Statement: the competition with highest points scored is played on April 20.
Function Chain: f_add_column(points scored) -> f_select_row(*) -> f_select_column(when, points scored) -> f_sort_column(points scored) -> <END>

/*
col : iso/iec standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2011) | 7
*/
Statement: 2 standards are published in 2011
Function Chain: f_add_column(year) -> f_select_row(row 3) -> f_select_column(year) -> f_group_column(year) -> <END>

Here are examples of using the operations to tell whether the statement is True or False."""

possible_next_operation_dict = {
    "<init>": [
        "add_column", 
        "select_row", 
        "select_column",
        "group_column",
        "sort_column",
    ],
    "add_column": [
        "select_row",
        "select_column", 
        "group_column", 
        "sort_column",
        "<END>",
    ],
    "select_row": [
        "select_column",
        "group_column",
        "sort_column",
        "<END>",
    ],
    "select_column": [
        "group_column",
        "sort_column",
        "<END>",
    ],
    "group_column": [
        "sort_column",
        "<END>",
    ],
    "sort_column": [
        "<END>",
    ],
}




########################################################################################################################################################################################################################
########################################################################################################################################################################################################################
########################################################################################################################################################################################################################
########################################################################################################################################################################################################################


# WIKITQ
wikitq_natural_language_plan_demo = """
We are working on WikiTQ dataset.
Your task is to develop step-by-step plan to answer the given question based on the provided table.
There exists data where smaller values indicate better, greater, or more favorable conditions, such as rankings, times, error rates, etc.

Here are example plans you can refer to:

### Table:
/*
col : id | name | hometown
row 1 : 1 | alice | new york
row 2 : 2 | bob | los angeles
row 3 : 3 | charlie | chicago
*/
Question: which players are from chicago?
Plan:
1. Select rows where the 'hometown' is 'chicago'.
2. Select the 'name' column.

### Table:
/*
col : id | name | score
row 1 : 1 | alice | 85
row 2 : 2 | bob | 90
row 3 : 3 | charlie | 75
*/
Question: what is the score of alice?
Plan:
1. Select rows where the 'name' is 'alice'.
2. Select the 'score' column.

### Table:
/*
col : id | name | salary
row 1 : 1 | alice | $95,000
row 2 : 2 | bob | $105,000
row 3 : 3 | charlie | $88,000
*/
Question: how many employees earn more than $100,000?
Plan:
1. Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
2. Select rows where the 'num_salary' is greater than 100000.
3. Count the number of rows.

### Table:
/*
col : id | name | salary
row 1 : 1 | alice | $95,000
row 2 : 2 | bob | $105,000
row 3 : 3 | charlie | $88,000
*/
Question: what is the average salary?
Plan:
1. Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
2. Calculate the average salary from the 'num_salary' column.

### Table:
/*
col : place | player | score
row 1 : 1 | hale irwin | 68 + 68 = 136
row 2 : 2 | fuzzy zoeller | 71 + 66 = 137
row 3 : t3 | david canipe | 69 + 69 = 138
*/
Question: who had the highest score?
Plan:
1. Extract the numerical score from the 'score' column then add column 'num_score' to existing table.
2. Order the table by 'num_score' in descending order.
3. Select row number 1.
4. Select the 'player' column.

### Table:
/*
col : place | player | score
row 1 : 1 | hale irwin | 68 + 68 = 136
row 2 : 2 | fuzzy zoeller | 71 + 66 = 137
row 3 : t3 | david canipe | 69 + 69 = 138
*/
Question: what is the highest score?
Plan:
1. Extract the numerical score from the 'score' column then add column 'num_score' to existing table.
2. Calculate the highest score from the 'num_score' column.

### Table:
/*
col : rank | athlete | time
row 1 : 1 | manjeet kaur (ind) | 52.17
row 2 : 2 | olga tereshkova (kaz) | 51.86
row 3 : 3 | pinki pramanik (ind) | 53.06
*/
Question: how many athletes from india participated in?
Plan:
1. Select rows where 'athlete' is 'ind' using LIKE function.
2. Count the number of rows.

### Table:
/*
col : game_id | venue | date
row 1 : 1 | orlando | 2024-11-23
row 2 : 2 | new york | 2022-09-12
row 3 : 3 | san jose | 2024-09-11
*/
Question: how many games were played on different dates?
Plan:
1. Count the number of distinct dates from the 'date' column.

### Table:
/*
col : id | product | region | sales
row 1 : 1 | laptop | north | 100
row 2 : 2 | tablet | south | 150
row 3 : 3 | smartphone | north | 200
*/
Question: what are the total sales in the north region?
Plan:
1. Select rows where 'region' is 'north'.
2. Sum the sales from the 'sales' column.

### Table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 85
row 2 : 2 | bob | math | 90
row 3 : 3 | charlie | math | 80
*/
Question: what is the score of charlie in math?
Plan:
1. Select rows where 'student' is 'charlie' and 'subject' is 'math'.
2. Select the 'score' column.

### Table:
/*
col : id | product | quarter | sales
row 1 : 1 | laptop | Q1 | 100000
row 2 : 2 | tablet | Q1 | 150000
row 3 : 3 | smartphone | Q1 | 120000
*/
Question: which product had the highest sales in Q2?
Plan:
1. Select rows where 'quarter' is 'Q2'.
2. Order the table by 'sales' in descending order.
3. Select row number 1.
4. Select the 'product' column.

### Table:
/*
col : author | genre | books_sold
row 1 : smith | fiction | 300
row 2 : doe | fiction | 400
row 3 : roe | non-fiction | 500
*/
Question: which genre had the highest book sales?
Plan:
1. Order the table by 'books_sold' in descending order.
2. Select row number 1.
3. Select the 'genre' column.

### Table:
/*
col : employee | department | money_per_hour
row 1 : alice | hr | 50.55
row 2 : bob | hr | 55.75
row 3 : charlie | it | 60.33
*/
Question: who earned the most money per hour in 2018?
Plan:
1. Order the table by 'money_per_hour' in descending order.
2. Select row number 1.
3. Select the 'employee' column.

### Table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 85
row 2 : 2 | bob | math | 90
row 3 : 3 | charlie | math | 80
*/
Question: who has the third highest score in math?
Plan:
1. Order the table by 'score' in descending order.
2. Select rows where 'subject' is 'math'.
3. Select row number 3.
4. Select the 'student' column.

### Table:
/*
col : id | runner | country | time
row 1 : 1 | alice | usa | 2:45:30
row 2 : 2 | bob | kenya | 2:12:45
row 3 : 3 | charlie | uk | 2:35:10
*/
Question: who had the fastest time in the marathon?
Plan:
1. Extract the number of seconds from the 'time' column then add column 'secs' to existing table.
2. Order the table by 'secs' in ascending order.
3. Select row number 1.
4. Select the 'runner' column.

### Table:
/*
col : id | runner | country | time
row 1 : 1 | alice | usa | 2:45:30
row 2 : 2 | bob | kenya | 2:12:45
row 3 : 3 | charlie | uk | 2:35:10
*/
Question: how long does it take for bob to finish?
Plan:
1. Select rows where 'runner' is 'bob'.
2. Select the 'time' column.

### Table:
/*
col : name | position | league_apps | total_apps
row 1 : mike maginan | df | 0 | 0
row 2 : tommy chris | df | 46 | 52
row 3 : johny lowe | mf | 39 | 44
*/
Question: how many players have total apps more than 50?
Plan:
1. Select rows where 'total_apps' is greater than 50.
2. Count the number of rows.

### Table:
/*
col : id | project | department | deadline
row 1 : 1 | migration | it | 2023-12-01
row 2 : 2 | rebranding | marketing | 2023-11-15
row 3 : 3 | audit | finance | 2023-12-20
*/
Question: which project has the latest deadline?
Plan:
1. Order the table by 'deadline' in descending order.
2. Select row number 1.
3. Select the 'project' column.

### Table:
/*
col : id | project | department | deadline
row 1 : 1 | migration | it | 2023-12-01
row 2 : 2 | rebranding | marketing | 2023-11-15
row 3 : 3 | audit | finance | 2023-12-20
*/
Question: when is the dealine for rebrand?
Plan:
1. Select rows where 'project' is 'rebrand'.
2. Select the 'deadline' column.

### Table:
/*
col : id | conference | location | attendance
row 1 : 1 | conf A | san francisco | 32000
row 2 : 2 | conf B | new york | 34000
row 3 : 3 | conf C | chicago | 31000
*/
Question: how many conferences had more than 30000 attendees?
Plan:
1. Select rows where 'attendance' is greater than 30000.
2. Count the number of rows.

### Table:
/*
col : student_id | name | subject | grade | year
row 1 : 1 | alice | math | a | 2021
row 2 : 2 | bob | math | b | 2021
row 3 : 3 | charlie | science | a | 2021
*/
Question: how many students got an 'a' in math?
Plan:
1. Select rows where 'subject' is 'math' and 'grade' is 'a'.
2. Count the number of rows.

### Table:
/*
col : product_id | product_name | launch_date | units_sold
row 1 : 1 | phone x | 2021-09-01 | 10000
row 2 : 2 | laptop y | 2021-08-15 | 15000
row 3 : 3 | tablet z | 2021-07-20 | 12000
*/
Question: which product had the highest units sold?
Plan:
1. Order the table by 'units_sold' in descending order.
2. Select row number 1.
3. Select the 'product_name' column.

### Table:
/*
col : id | model | year | sales
row 1 : 1 | model a | 2021 | 50000
row 2 : 2 | model b | 2020 | 60000
row 3 : 3 | model c | 2021 | 55000
*/
Question: what is the total sales for all cars in 2021?
Plan:
1. Select rows where 'year' is 2021.
2. Sum the sales from the 'sales' column.

### Table:
/*
col : movie_id | title | genre | rating
row 1 : 1 | movie a | action | 8.5
row 2 : 2 | movie b | drama | 7.8
row 3 : 3 | movie c | comedy | 6.9
*/
Question: which movie has the lowest rating?
Plan:
1. Order the table by 'rating' in ascending order.
2. Select row number 1.
3. Select the 'title' column.

### Table:
/*
col : ranking | title | genre
row 1 : 1 | movie a | action
row 2 : 2 | movie b | drama
row 3 : 3 | movie c | comedy
*/
Question: which movies are top-2 best ranked?
Plan:
1. Order the table by 'ranking' in ascending order.
2. Select row number 1 and 2.
3. Select the 'title' column.

### Table:
/*
col : year | team | goals_scored | goals_conceded
row 1 : 2018 | france | 14 | 4
row 2 : 2014 | germany | 18 | 7
row 3 : 2010 | spain | 8 | 2
*/
Question: which team had the most goals scored in the world cup?
Plan:
1. Order the table by 'goals_scored' in descending order.
2. Select row number 1.
3. Select the 'team' column.

### Table:
/*
col : year | school | graduates | dropouts
row 1 : 2020 | school a | 200 | 20
row 2 : 2019 | school b | 180 | 25
row 3 : 2021 | school a | 220 | 15
*/
Question: which year had the highest number of graduates from school a?
Plan:
1. Select rows where 'school' is 'school a'.
2. Order the table by 'graduates' in descending order.
3. Select row number 1.
4. Select the 'year' column.

### Table:
/*
col : quarter | revenue | expenses | profit
row 1 : Q1 | 100000 | 50000 | 50000
row 2 : Q2 | 150000 | 70000 | 80000
row 3 : Q3 | 200000 | 90000 | 110000
*/
Question: which quarter had the highest profit?
Plan:
1. Order the table by 'profit' in descending order.
2. Select row number 1.
3. Select the 'quarter' column.

### Table:
/*
col : airport_code | city | passengers | flights
row 1 : jfk | new york | 300000 | 2000
row 2 : lax | los angeles | 350000 | 1800
row 3 : ord | chicago | 250000 | 2200
*/
Question: which airport had the highest number of passengers?
Plan:
1. Order the table by 'passengers' in descending order.
2. Select row number 1.
3. Select the 'airport_code' column.
"""

#########################


wikitq_natural_language_step_to_sql_demo = """
We are working on the task of converting natural language action into SQL command.

###
Given this table:
/*
col : competition | date | location | attendance
row 1 : conference 1 | 2024-06-01 | new york | 32092
row 2 : conference 2 | 2024-06-15 | san francisco | 34186
row 3 : conference 3 | 2024-07-20 | chicago | 17503
*/

Write a SQL command that: Extract the 'year' from the 'date' column then add column 'year' to existing table.

SQL is:
```sql
SELECT *,
       STRFTIME('%Y', date) AS year
FROM table_sql;
--  Extract the 'year' from the 'date' column then add column 'year' to existing table.
```

###
Given this table:
/*
col : id | name | department | salary | years
row 1 : 1 | alice | it | $95,000 | 3
row 2 : 2 | bob | finance | $105,000 | 5
row 3 : 3 | charlie | marketing | $88,000 | 2
*/

Write a SQL command that: Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.

SQL is:
```sql
SELECT *,
    CAST(REPLACE(REPLACE(salary, '$', ''), ',', '') AS INTEGER) AS num_salary
FROM table_sql;
-- Extract the numerical value from the 'salary' column then add column 'num_salary' to existing table.
```

###
Given this table:
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | e
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | +3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | +2
row 4 : t4 | james canpo | france | 35 + 45 = 80 | -2
*/

Write a SQL command that: Select rows where 'score' is '68 + 68'

SQL is:
```sql
SELECT *
FROM table_sql
WHERE score LIKE '%68 + 68%';
-- Select rows where 'score' is '68 + 68'
```

###
Given this table:
/*
col : ranking | title | genre
row 1 : 1 | movie a | action
row 2 : 2 | movie b | drama
row 3 : 3 | movie c | comedy
*/

Write a SQL command that: Select row number 1 and 2.

SQL is:
```sql
SELECT * 
FROM table_sql
LIMIT 2;
-- Select row number 1 and 2.
```

###
Given this table:
/*
col : rank | player | games | scores
row 1 : 1 | alex smith | 45 | 23.4(11)
row 2 : 2 | john doe | 43 | 14.2(8)
row 3 : 3 | jane doe | 32 | 9.6(6)
row 4 : 4 | emily johnson | 17 | 3.2(3)
*/

Write a SQL command that: Select rows where 'player' is not 'jane doe'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE player != 'jane doe';
-- Select rows where 'player' is not 'jane doe'.
```

###
Given this table:
/*
col : rank | player | games | scores
row 1 : 1 | alex smith | 45 | 23.4(11)
row 2 : 2 | john doe | 43 | 14.2(8)
row 3 : 3 | jane doe | 32 | 9.6(6)
row 4 : 4 | emily johnson | 17 | 3.2(3)
*/

Write a SQL command that: Select rows where 'games' is not 16.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE games != 16;
-- Select rows where 'games' is not 16.
```

###
Given this table:
/*
col : match_id | home_team | away_team | score | crowd_size
row 1 : 1 | bulls | lakers | 102-95 | 18000
row 2 : 2 | heat | celtics | 88-90 | 20000
row 3 : 3 | nets | warriors | 110-112 | 21000
row 4 : 4 | knicks | suns | 95-99 | 15000
row 5 : 5 | clippers | raptors | 105-100 | 17000
*/

Write a SQL command that: Extract the home score from the 'score' column then add column 'home_score' to the existing table.

SQL is:
```sql
SELECT *,
    CAST(SUBSTR(score, 1, INSTR(score, '-') - 1) AS INTEGER) AS home_score
FROM table_sql;
-- Extract the home score from the 'score' column then add column 'home_score' to the existing table.
```

###
Given this table:
/*
col : match_id | home_team | away_team | score | crowd_size
row 1 : 1 | bulls | lakers | 102-95 | 18000
row 2 : 2 | heat | celtics | 88-90 | 20000
row 3 : 3 | nets | warriors | 110-112 | 21000
row 4 : 4 | knicks | suns | 95-99 | 15000
row 5 : 5 | clippers | raptors | 105-100 | 17000
*/

Write a SQL command that: Extract the total crowd size from the 'crowd_size' column then add column 'total_crowd_size' to the existing table.

SQL is:
```sql
SELECT *,
    (SELECT SUM(crowd_size) FROM table_sql) AS total_crowd_size
FROM table_sql;
-- Extract the total crowd size from the 'crowd_size' column then add column 'total_crowd_size' to the existing table.
```

###
Given this table:
/*
col : id | name | department | salary | years
row 1 : 1 | alice | it | 95000 | 3
row 2 : 2 | bob | finance | 105000 | 5
row 3 : 3 | charlie | marketing | 88000 | 2
*/

Write a SQL command that: Select rows where the 'salary' is greater than 100000.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE salary > 100000;
-- Select rows where the 'salary' is greater than 100000.
```

###
Given this table:
/*
col : when | competition | venue | position | notes
row 1 : 2014-01-01 | city marathon | new york, usa | 2nd | 2:30:45
row 2 : 2015-01-01 | international marathon | london, uk | 1st | 2:25:30
row 3 : 2017-01-01 | national marathon | berlin, germany | 5th | 2:35:10
row 4 : 2020-01-01 | city marathon | tokyo, japan | 3rd | 2:28:40
row 5 : 2022-01-01 | olympic games | paris, france | 4th | 2:32:00
*/

Write a SQL command that: Select rows where 'competition' is 'marathon'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE competition LIKE '%marathon%';
-- Select rows where 'competition' is 'marathon'.
```

###
Given this table:
/*
col : game_id | venue | when | attendance | team | game
row 1 : 1 | orlando | 2024-11-23 | 52000 | magic | away
row 2 : 2 | new york | 2022-09-12 | 48000 | knicks | away
row 3 : 3 | orlando | 2024-09-11 | 50000 | tigers | away
*/

Write a SQL command that: Extract the number of distinct dates from the 'when' column then add column 'date_cnt' to existing table.

SQL is:
```sql
SELECT *, 
       (SELECT COUNT(DISTINCT "when") FROM table_sql) AS date_cnt
FROM table_sql;
-- Extract the number of distinct dates from the 'when' column to add column 'date_cnt' to existing table.
```

###
Given this table:
/*
col : id | name | hometown | score
row 1 : 1 | alice | new york | 85
row 2 : 2 | bob | los angeles | 90
row 3 : 3 | charlie | chicago | 75
row 4 : 4 | dave | new york | 88
row 5 : 5 | eve | los angeles | 92
*/

Write a SQL command that: Select rows where the 'name' is 'bob' or 'charlie'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE name LIKE '%bob%' OR name LIKE '%charlie%';
-- Select rows where the 'name' is 'bob' or 'charlie'.
```

###
Given this table:
/*
col : id | name | department | score
row 1 : 1 | alice | hr | 90
row 2 : 2 | bob | it | 80
row 3 : 3 | charlie | finance | 88
row 4 : 4 | dave | marketing | 70
row 5 : 5 | eve | hr | 95
*/

Write a SQL command that: Extract the average of the 'score' column then add column 'avg_score' to existing table.

SQL is:
```sql
SELECT *, 
    (SELECT AVG(score) FROM table_sql) AS avg_score
FROM table_sql;
-- Extract the average of the 'score' column then add column 'avg_score' to existing table.
```

###
Given this table:
/*
col : id | runner | country | time
row 1 : 1 | alice | usa | 2:45:30
row 2 : 2 | bob | kenya | 2:12:45
row 3 : 3 | charlie | uk | 2:35:10
*/

Write a SQL command that: Extract the number of seconds from the 'time' column then add column 'secs' to existing table.

SQL is:
```sql
SELECT *,
       CAST(SUBSTR(time, 1, 2) AS INTEGER) * 3600 + 
       CAST(SUBSTR(time, 4, 2) AS INTEGER) * 60 + 
       CAST(SUBSTR(time, 7, 2) AS INTEGER) AS secs
FROM table_sql;
-- Extract the number of seconds from the 'time' column then add column 'secs' to existing table.
```

###
Given this table:
/*
col : game | winner | result
row 1 : 1 | alex smith | 45-23
row 2 : 2 | john doe | 43-14
row 3 : 3 | jane doe | 32-9
row 4 : 4 | emily johnson | 17-23
*/

Write a SQL command that: Extract the numerical total score from the 'result' column by adding the two numbers then add column 'total_score' to existing table.

SQL is:
```sql
SELECT *,
       CAST(SUBSTR(result, 1, INSTR(result, '-') - 1) AS INTEGER) + 
       CAST(SUBSTR(result, INSTR(result, '-') + 1) AS INTEGER) AS total_score
FROM table_sql;
-- Extract the numerical total score from the 'result' column by adding the two numbers then add column 'total_score' to existing table.
```

###
Given this table:
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | e
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | +3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | +2
row 4 : t4 | james canpo | france | 35 + 45 = 80 | -2
*/
Write a SQL command that: Select rows where 'country' is 'france' or 'player' is 'james canpo'.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE country LIKE '%france%' OR player LIKE '%james canpo%';
-- Select rows where 'country' is 'france' or 'player' is 'james canpo'.
```

###
Given this table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 90
row 2 : 2 | bob | math | 80
row 3 : 3 | charlie | math | 80
row 4 : 4 | dave | math | 75
*/

Write a SQL command that: Select row number 1.

SQL is:
```sql
SELECT *
FROM table_sql
LIMIT 1 OFFSET 0;
-- Select row number 1.
```

###
Given this table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 90
row 2 : 2 | bob | math | 80
row 3 : 3 | charlie | math | 80
row 4 : 4 | dave | math | 75
*/

Write a SQL command that: Select row number 3.

SQL is:
```sql
SELECT *
FROM table_sql
LIMIT 1 OFFSET 2;
-- Select row number 3.
```

###
Given this table:
/*
col : id | name | hometown | score
row 1 : 1 | alice | new york | 85
row 2 : 2 | bob | los angeles | 90
row 3 : 3 | charlie | chicago | 75
row 4 : 4 | dave | new york | 88
row 5 : 5 | eve | los angeles | 92
*/

Write a SQL command that: Order the table by 'score' in descending order.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY score DESC;
-- Order the table by 'score' in descending order.
```

###
Given this table:
/*
col : competition | date | location | attendance
row 1 : conference 1 | 2024-06-01 | new york | 3.21
row 2 : conference 2 | 2024-06-15 | san francisco | 3.41
row 3 : conference 3 | 2024-07-20 | chicago | 1.75
*/

Write a SQL command that: Order the table by 'attendance' in descending order.

SQL is:
```sql
SELECT *
FROM table_sql
ORDER BY CAST(attendance AS REAL) DESC;
-- Order the table by 'attendance' in descending order.
```

###
Given this table:
/*
col : rank | player | games | scores
row 1 : 1 | alex smith | 112 | 1100
row 2 : 2 | john doe | 107 | 1050
row 3 : 3 | jane doe | 131 | 980
row 4 : 4 | emily johnson | 116 | 20
*/

Write a SQL command that: Select rows where 'rank' is greater than 2.

SQL is:
```sql
SELECT *
FROM table_sql
WHERE rank > 2;
-- Select rows where 'rank' is greater than 2.
```

###
Given this table:
/*
col : id | name | department | score | min_score
row 1 : 1 | alice | hr | 90 | 70
row 2 : 2 | bob | it | 70 | 70
row 3 : 3 | charlie | finance | 88 | 70
row 4 : 4 | dave | marketing | 70 | 70
row 5 : 5 | eve | hr | 95 | 70
*/

Write a SQL command that: Select rows where the 'score' is equal to 'min_score'.

SQL is:
```sql
SELECT * FROM table_sql WHERE score = min_score;
-- Select rows where the 'score' is equal to 'min_score'.
```

###
Given this table:
/*
col : place | player | country | score | to_par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | -4
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | -3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | -2
*/

Write a SQL command that: Extract the numerical score value from 'score' column then add a column 'num_score' to existing table.

SQL is:
```sql
SELECT *,
       CAST(SUBSTR(score, INSTR(score, '=') + 2) AS INT) AS num_score
FROM table_sql;
-- Extract the numerical score value from 'score' column then add a column 'num_score' to existing table.
```

###
Given this table:
/*
col : id | name | salary
row 1 : 1 | alice | $95,000
row 2 : 2 | bob | $105,000
row 3 : 3 | charlie | $88,000
*/

Write a SQL command that: Count the number of rows.

SQL is:
```sql
SELECT COUNT(*) FROM table_sql;
-- Count the number of rows.
```

###
Given this table:
/*
col : id | name | score
row 1 : 1 | alice | 85
row 2 : 2 | mendy | 80
row 3 : 3 | adrea | 50
*/

Write a SQL command that: Select the 'score' column.

SQL is:
```sql
SELECT score FROM table_sql;
-- Select the 'score' column.
```

###
Given this table:
/*
col : game_id | venue | date | num_date
row 1 : 1 | orlando | 2024-11-23 | 3
*/

Write a SQL command that: Select the 'num_date' column.

SQL is:
```sql
SELECT num_date FROM table_sql;
-- Select the 'num_date' column.
```

###
Given this table:
/*
col : id | student | subject | score
row 1 : 1 | alice | math | 85
row 2 : 2 | bob | math | 90
row 3 : 3 | charlie | math | 80
*/

Write a SQL command that: Select rows where 'student' is 'charlie' and 'subject' is 'math'.

SQL is:
```sql
SELECT * 
FROM table_sql 
WHERE student = 'charlie' AND subject = 'math';
-- Select rows where 'student' is 'charlie' and 'subject' is 'math'.
```

###
Given this table:
/*
col : game_id | venue | date
row 1 : 1 | orlando | 2024-11-23
row 2 : 2 | new york | 2022-09-12
row 3 : 3 | san jose | 2024-09-11
*/

Write a SQL command that: Count the number of distinct dates from the 'date' column.

SQL is:
```sql
SELECT COUNT(DISTINCT date) AS distinct_date_count
FROM table_sql;
-- Count the number of distinct dates from the 'date' column.
```

### Table:
/*
col : id | product | region | sales
row 1 : 1 | laptop | north | 100
row 2 : 2 | tablet | south | 150
row 3 : 3 | smartphone | north | 200
*/

Write a SQL command that: Sum the sales from the 'sales' column.

SQL is:
```sql
SELECT SUM(sales) AS total_sales
FROM table_sql;
-- Sum the sales from the 'sales' column.
```

###
Given this table:
/*
col : student_id | name | age | grade
row 1 : 1 | john | 15 | 10
row 2 : 2 | jane | 14 | 9
row 3 : 3 | doe | 16 | 11
*/

Write a SQL command that: Calculate the average age from the 'age' column.

SQL is:
```sql
SELECT AVG(age) AS average_age
FROM table_sql;
-- Calculate the average age from the 'age' column.
```

###
Given this table:
/*
col : order_id | customer | amount
row 1 : 1 | alice | 250
row 2 : 2 | bob | 300
row 3 : 3 | charlie | 150
*/

Write a SQL command that: Sum the orders from the 'amount' column.

SQL is:
```sql
SELECT SUM(amount) AS total_amount
FROM table_sql;
-- Sum the orders from the 'amount' column.
```

###
Given this table:
/*
col : employee_id | name | department | salary
row 1 : 1 | max | hr | 5000
row 2 : 2 | kate | it | 6000
row 3 : 3 | luke | finance | 7000
*/

Write a SQL command that: Calculate the highest salary from the 'salary' column.

SQL is:
```sql
SELECT MAX(salary) AS highest_salary
FROM table_sql;
-- Calculate the highest salary from the 'salary' column.
```
"""