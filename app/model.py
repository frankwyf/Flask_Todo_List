from app import db

# defining objects for database
class Todoers(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200))
    Email = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, default=False)



    def __int__(self, username, Email, status, password):
        self.username = username
        self.Email = Email
        self.status = stauts
        self.password = password


class Task(db.Model):
    taskID = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True)  # primary key of every task
    module = db.Column(db.String(200), nullable=False)  # module title
    assessment = db.Column(db.String(200), nullable=False)  # assessment title
    create_date = db.Column(db.DateTime)  # create time
    ddl = db.Column(db.DateTime)  # dead line time
    remind = db.Column(db.DateTime)  # when to remind the user
    description = db.Column(db.String(200))  # description of the task
    # priority of the task, four levels in total
    priority = db.Column(db.Integer, default=1)
    # mark as uncomplete (0) as default
    status = db.Column(db.Integer, default=0)
    # build the foreign key between two tables
    host = db.Column(db.Integer, db.ForeignKey('todoers.id'), nullable=False)

    def __int__(
            self,
            taskID,
            module,
            assessment,
            create_date,
            ddl,
            status,
            remind,
            description,
            prority):
        self.taskID = taskID
        self.module = module
        self.assessment = assessment
        self.create_date = create_date
        self.ddl = ddl
        self.status = status
        self.remind = remind
        self.description = description
        self.priority = prority
