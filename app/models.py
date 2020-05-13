from app import db, login, ma, app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import UserMixin
from time import time
import jwt
from hashlib import md5
from time import time
from flask import current_app
import os
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import io
from io import StringIO
from cryptography.fernet import Fernet


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64), index=True, unique=True)
        admin_status = db.Column(db.Integer)
        user_enc = db.Column(db.String(44))
        email = db.Column(db.String(120), index=True, unique=True)
        password_hash = db.Column(db.String(128))
        aim_training_tool_user_status = db.Column(db.Integer)
        academy_club_status = db.Column(db.Integer)
        trophies_list = db.Column(db.String(500))

        training_instances = db.relationship('TrainingInstance', backref='author', lazy='dynamic')

        def __repr__(self):
                return '<User {}>'.format(self.username)
        def set_name_encrypt(self):
            self.user_enc = b'y7W71MtNiM6U6S0l1Pmo1mdMlYnDG38miOKt5a0aXq4='

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

        def get_trophies_list(self, trophies_list):
            list_of_trophies = trophies_list.split(';')
            return list_of_trophies

        #need set trophy list method

        def add_trophy_to_list(self, list_of_trophies, trophy):
            if trophy not in list_of_trophies:
                list_of_trophies = list_of_trophies.append(trophy)

        def get_reset_password_token(self, expires_in=600):
            return jwt.encode(
                {'reset_password': self.id, 'exp': time() + expires_in}, current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

        def read_input_data(self, path):

                subfiles = [StringIO()] 
                with open(path) as bigfile:
                        count = 0
                        for line in bigfile:
                                if line.strip() == "" and count != 0: # blank line, new subfile  
                                        subfiles.append(StringIO())
                                elif line.strip() == "" and count == 0: 
                                        continue
                                else: # continuation of same subfile                                                                                                                                                   
                                        subfiles[-1].write(line)
                                count=count+1
                
                #Method to go through each subfile and create Clicks classes and get relevant info
                return subfiles

        def get_existing_scenario_instances(self):
            results = db.session.query(TrainingInstance.session_file_name).filter_by(user_id = self.id)
            list_of_results = [r for r, in results]
            return list_of_results

        def add_all_new_sessions(self, all_scenarios_df, files):
            existing_session_instances = self.get_existing_scenario_instances()
            new_files =0
            for file in files:
                # Check if the file is one of the allowed types/extensions
                if file and allowed_file(file.filename):

                    # Make the filename safe, remove unsupported chars
                    filename = secure_filename(file.filename)

                    if filename not in existing_session_instances:
                        new_file = new_file+1

                        # Save the filename into a list, we'll use it later
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                        subfile = self.read_input_data(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        new_session = TrainingInstance()
                        new_session.session_file_name = filename
                        new_session.user_id = self.id 
                        new_session.date_time = new_session.get_date_time(filename) #date and time of session
                                                                 
                        shot_summary_list = new_session.collect_shots_damage_data(subfile)
                        summary_stats_list = new_session.collect_summary_stats_data(subfile)
                        settings_data_list = new_session.collect_settings_data(subfile)

                        new_session.sum_shots = shot_summary_list[0]
                        new_session.sum_hits = shot_summary_list[1]
                        new_session.accuracy = new_session.sum_hits/new_session.sum_shots
                        new_session.sum_damage_done = shot_summary_list[2]
                        new_session.sum_damage_possible = shot_summary_list[3]
                        
                        new_session.kills = summary_stats_list[0]
                        new_session.deaths = summary_stats_list[1]
                        new_session.fight_time = summary_stats_list[2]
                        new_session.avg_ttk = summary_stats_list[3]
                        new_session.dmg_done = summary_stats_list[4]
                        new_session.dmg_taken = summary_stats_list[5]
                        new_session.midairs = summary_stats_list[6]
                        new_session.midaired = summary_stats_list[7]
                        new_session.directs = summary_stats_list[8]
                        new_session.directed = summary_stats_list[9]
                        new_session.distance_traveled = summary_stats_list[10]
                        new_session.score = summary_stats_list[11]
                        new_session.scenario = summary_stats_list[12]
                        new_session.hash_no = summary_stats_list[13]
                        new_session.game_version = summary_stats_list[14]
                        
                        new_session.input_lag = settings_data_list[0]
                        new_session.max_fps_config = settings_data_list[1]
                        new_session.sens_scale = settings_data_list[2]
                        new_session.horiz_sens = settings_data_list[3]
                        new_session.vert_sens = settings_data_list[4]
                        new_session.fov = settings_data_list[5]

                        if new_session.scenario in list(all_scenarios_df.scenario_name):
                                current_scenario = all_scenarios_df.loc[all_scenarios_df['scenario_name']==new_session.scenario]
                                current_scenario = current_scenario.values.tolist()[0]

                                new_session.scenario_id = current_scenario[0]
                                new_session.scenario_type = current_scenario[2]
                                new_session.scenario_level = current_scenario[3]
                                new_session.scenario_direction = current_scenario[4]
                                new_session.scenario_fov = current_scenario[5]
                                new_session.scenario_skills_tags = current_scenario[6]
                                new_session.scenario_click_data = current_scenario[7]
                                new_session.scenario_target_acquisition = current_scenario[8]

                        else:
                                new_session.scenario_id = None
                                new_session.scenario_type = None
                                new_session.scenario_level = None
                                new_session.scenario_direction = None
                                new_session.scenario_fov = None
                                new_session.scenario_skills_tags = None
                                new_session.scenario_click_data = None
                                new_session.scenario_target_acquisition = None

                        db.session.add(new_session)
                        db.session.commit()
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            return new_files

        def add_videos_table(self):
            db.session.query(Videos).delete()
            db.session.commit()
            videos_table = pd.read_csv('video_list.csv')
            videos_table = videos_table.where(videos_table.notnull(), None)

            for x in videos_table.to_dict('records'):

                new_video = Videos()
                new_video.video_url = x['video_url']
                new_video.video_title = x['video_title']
                new_video.video_description = x['video_description']
                new_video.video_channel_name = x['video_channel_name']
                new_video.video_channel_url = x['video_channel_url']
                new_video.date_added_n1 = new_video.get_date_time(x['date_added_n1'])
                new_video.game = x['game']
                new_video.difficulty = x['difficulty']
                new_video.timestamps = x['timestamps']
                new_video.featured_video_tag = int(x['featured_video_tag'])
                new_video.best_new_video_tag = int(x['best_new_video_tag'])
                new_video.n1_original_content_tag = int(x['n1_original_content_tag'])
                new_video.n1_select_tag = int(x['n1_select_tag'])
                new_video.n1_description = x['n1_description']
                new_video.tags = x['tags']

                db.session.add(new_video)
                db.session.commit()
            
        def update_scenarios_table(self, admin_status, csv_file):
            if admin_status == 1:
                db.session.query(Scenarios).delete()
                db.session.commit()
                scenarios_table = pd.read_csv(csv_file)
                scenarios_table = scenarios_table.where(pd.notnull(scenarios_table), None)
                scenarios = [Scenarios(**x) for x in scenarios_table.to_dict('records')]
                for scenario in scenarios:
                    db.session.add(scenario)
                    db.session.commit()

        @staticmethod
        def verify_reset_password_token(token):
            try:
                id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
            except:
                return

            return User.query.get(id)

class Videos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_url=db.Column(db.String(11))
    video_title=db.Column(db.String(100))
    video_description=db.Column(db.String(5000))
    video_channel_name=db.Column(db.String(100))
    video_channel_url=db.Column(db.String(24))
    date_added_n1=db.Column(db.DateTime)
    game=db.Column(db.String(100))
    difficulty=db.Column(db.String(100))
    timestamps=db.Column(db.String(5000))
    featured_video_tag=db.Column(db.Integer)
    best_new_video_tag=db.Column(db.Integer)
    n1_original_content_tag=db.Column(db.Integer)
    n1_select_tag=db.Column(db.Integer)
    n1_description=db.Column(db.String(1000))
    tags=db.Column(db.String(500))
    homepage_bestnew = db.Column(db.Integer)
    homepage_staffpick = db.Column(db.Integer)


    def __repr__(self):
        return '<Video {}>'.format(self.video_title)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_date_time(self, date_string):
        return datetime.strptime(date_string, '%m/%d/%Y')

class Playlists(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_date_created = db.Column(db.DateTime, index=True)
    playlist_name = db.Column(db.String(200))
    playlist_description = db.Column(db.String(5000))
    list_of_videos = db.Column(db.String(200))
    playlist_img_src = db.Column(db.String(100))
    playlist_author_id = db.Column(db.Integer)
    playlist_author_name = db.Column(db.String(50))
    playlist_difficulty = db.Column(db.String(14))
    homepage_featured = db.Column(db.Integer)

    def __repr__(self):
        return '<Playlist {}>'.format(self.video_title)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_date_time(self, date_string):
        return datetime.strptime(date_string, '%m/%d/%Y')

class Scenarios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scenario_name = db.Column(db.String(100))
    scenario_type = db.Column(db.String(32))
    scenario_level = db.Column(db.String(32))
    scenario_direction = db.Column(db.String(32))
    scenario_fov = db.Column(db.String(32))
    scenario_skills_tags = db.Column(db.String(200))
    scenario_click_data = db.Column(db.Integer)
    scenario_target_acquisition = db.Column(db.Integer)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return '<Scenario {}>'.format(self.scenario_name)

class TrainingInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_file_name = db.Column(db.String(200), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_time = db.Column(db.DateTime, index=True)
    sum_shots = db.Column(db.Integer)
    sum_hits = db.Column(db.Integer)
    accuracy = db.Column(db.Integer)
    sum_damage_done = db.Column(db.Float)
    sum_damage_possible = db.Column(db.Float)
    kills = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    fight_time = db.Column(db.Integer)
    avg_ttk = db.Column(db.Float)
    dmg_done = db.Column(db.Float)
    dmg_taken = db.Column(db.Float)
    midairs = db.Column(db.Integer)
    midaired = db.Column(db.Integer)
    directs = db.Column(db.Integer)
    directed = db.Column(db.Integer)
    distance_traveled = db.Column(db.Float)
    score = db.Column(db.Float)
    scenario = db.Column(db.String(200))
    hash_no = db.Column(db.String(100))
    game_version = db.Column(db.String(32))
    input_lag = db.Column(db.Integer)
    max_fps_config = db.Column(db.Float)
    sens_scale = db.Column(db.String(32))
    horiz_sens = db.Column(db.Float)
    vert_sens = db.Column(db.Float)
    fov = db.Column(db.Float)
    test = db.Column(db.Integer)
    scenario_id = db.Column(db.Integer)
    scenario_type = db.Column(db.String(32))
    scenario_level = db.Column(db.String(32))
    scenario_direction = db.Column(db.String(32))
    scenario_fov = db.Column(db.String(32))
    scenario_skills_tags = db.Column(db.String(200))
    scenario_click_data = db.Column(db.Integer)
    scenario_target_acquisition = db.Column(db.Integer)

    def __repr__(self):
        return '<TrainingInstance {}>'.format(self.session_file_name)

    def get_date_time(self, file_name):
        substring = file_name[-29:]
        substring = substring[:-10]

        return datetime.strptime(substring, '%Y.%m.%d-%H.%M.%S')
        
    def collect_clicks_data(self, subfiles):
            
        # Create list of clicks data for the first table if it exists
        list_of_clicks_data = []
        #first check to see that there are click data to create
        split_lines_clicks = subfiles[0].getvalue().splitlines()[1:]
        if len(split_lines_clicks) > 1:
                index_counter = 0 
                for line in split_lines_clicks:
                        click_data = line.split(',')
                        new_click = Clicks(index_counter,
                                         self.session_id,
                                         click_data[1], #Timestamp
                                         click_data[2], #Bot
                                         click_data[3], #Weapon
                                         click_data[4], #TTK
                                         click_data[5], #Shots
                                         click_data[6], #Hits
                                         click_data[7], #Accuracy
                                         click_data[8], #Damage Done
                                         click_data[9], #Damage Possible
                                         click_data[10], #Efficiency
                                         click_data[11], #Cheated
                                         )
                        list_of_clicks_data.append(new_click)
                        index_counter = index_counter+1
        return list_of_clicks_data
            
    def collect_shots_damage_data(self, subfiles):
            # Fill in summary data from second table
 
            lines = subfiles[1].getvalue().splitlines()[1:]
            list_of_lines = []
            for line in lines:
                    row_data = line.split(',')
                    row_data = [float(i) for i in row_data[1:5]]   
                    list_of_lines.append(row_data)
            
            df = pd.DataFrame(columns = ['sum_shots','sum_hits','sum_damage_done', 'sum_damage_possible'], data=list_of_lines)
            return list(df.sum())
    
    def collect_summary_stats_data(self, subfiles):
            split_lines_clicks = subfiles[2].getvalue().splitlines()
            summary_stats_dict = {}
            summary_stats_list = []
            for line in split_lines_clicks:
                    summary_data = line.split(',')
                    summary_stats_dict[summary_data[0][:-1]]=summary_data[1]
            
            summary_stats_list.extend((summary_stats_dict['Kills'], 
                                     summary_stats_dict['Deaths'],
                                     summary_stats_dict['Fight Time'],
                                     summary_stats_dict['Avg TTK'], 
                                     summary_stats_dict['Damage Done'], 
                                     summary_stats_dict['Damage Taken'], 
                                     summary_stats_dict['Midairs'],
                                     summary_stats_dict['Midaired'], 
                                     summary_stats_dict['Directs'], 
                                     summary_stats_dict['Directed'],
                                     summary_stats_dict['Distance Traveled'],
                                     summary_stats_dict['Score'],
                                     summary_stats_dict['Scenario'],
                                     summary_stats_dict['Hash'],
                                     summary_stats_dict['Game Version']))
                    
            return summary_stats_list
    
    def collect_settings_data(self, subfiles):
            split_lines_clicks = subfiles[3].getvalue().splitlines()
            settings_stats_dict = {}
            for line in split_lines_clicks:
                    click_data = line.split(',')
                    settings_stats_dict[click_data[0][:-1]]=click_data[1]
            
            return (settings_stats_dict['Input Lag'], 
                            settings_stats_dict['Max FPS (config)'],
                            settings_stats_dict['Sens Scale'], 
                            settings_stats_dict['Horiz Sens'], 
                            settings_stats_dict['Vert Sens'],
                            settings_stats_dict['FOV'])

class TrainingInstanceSchema(ma.Schema):
    class Meta:
        fields =('session_file_name',
        'user_id',
        'date_time',
        'sum_shots',
        'sum_hits',
        'accuracy',
        'sum_damage_done',
        'sum_damage_possible',
        'kills',
        'deaths',
        'fight_time',
        'avg_ttk',
        'dmg_done',
        'dmg_taken',
        'midairs',
        'midaired',
        'directs',
        'directed',
        'distance_traveled',
        'score',
        'scenario',
        'hash_no',
        'game_version',
        'input_lag',
        'max_fps_config',
        'sens_scale',
        'horiz_sens',
        'vert_sens',
        'fov',
        'test',
        'scenario_id',
        'scenario_type',
        'scenario_level',
        'scenario_direction',
        'scenario_fov',
        'scenario_skills_tags',
        'scenario_click_data',
        'scenario_target_acquisition')

        

