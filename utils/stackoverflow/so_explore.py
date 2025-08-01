import duckdb as dd

# dd.sql("select users.email, questions.question_id from './users.json' as users, './questions_answers_comments.json' as questions where questions.owner.user_id=users.user_id").show()
# dd.sql("select users.email, count(*) as question_count from './users.json' as users, './questions_answers_comments.json' as questions where questions.owner.user_id=users.user_id group by users.email order by question_count desc").show()
# dd.sql("select len(questions.answers) from './questions_answers_comments.json' as questions").show()

# dd.sql("select * from './questions_answers_comments.json' as questions where questions.question_id=1297").show()
# dd.sql("select len(questions.answers) from './questions_answers_comments.json' as questions where questions.question_id=1297").show()
# dd.sql("select select users.emil, questions.answers.owner from './questions_answers_comments.json' as questions where questions.question_id=1297").show()
# dd.sql("select questions.answers from './questions_answers_comments.json' as questions").show()
# dd.sql("select unnest(questions.answers).answer_id from './questions_answers_comments.json' as questions").show()
# dd.sql("select unnest(questions.answers, recursive := true) from './questions_answers_comments.json' as questions").show()
# dd.sql("select answer_id from (select unnest(questions.answers) from './questions_answers_comments.json' as questions)").show()
# count of answer per user
# dd.sql("select questions.answers from './questions_answers_comments.json' as questions where len(questions.answers) > 0").show()
# dd.sql("select answers.answer_id from './questions_answers_comments.json'" where len(answers) ).show()
# dd.sql("select answer_id from (select answers from './questions_answers_comments.json')").show()
# dd.sql("select users.email, count(*) as answer_count from (select unnest(questions.answers, recursive := true) from './questions_answers_comments.json' as questions) as answers, './users.json' as users where answers.user_id = users.user_id group by users.email order by answer_count desc").show()
# dd.sql("select tags.name, tags.count, age(to_timestamp(tags.last_activity_date)) from './tags.json' as tags order by tags.last_activity_date desc, tags.count desc").show()
# dd.sql("select questions.question_id, questions.title, from './discussions_to_add.json' as questions where list_contains(questions.tags, 'openshift')").show()
# dd.sql("select questions.question_id, questions.title, questions.tags from './discussions_to_add.json' as questions order by questions.question_id").show()
# dd.sql("select tags.name, tags.count, age(to_timestamp(tags.last_activity_date)) from './tags.json' as tags where tags.count < 2 order by tags.last_activity_date desc, tags.count desc").show()
dd.sql("select question_id, view_count from './questions_answers_comments.json' as questions where view_count >= 100 order by view_count desc").show()