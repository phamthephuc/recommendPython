from flask import Flask, request
from flask_restful import Resource, Api
# from flask.json import jsonify
import pandas as pd
from getDataFromDB import getListData, getListObject
import numpy
from initRecommend import recommendLocation, recommendLocationForUser, reRecommendLocationForUser
import _thread
from _operator import index

passcode = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJMb2dpbiIsImRhdGEiOnsiaWQiOjEyLCJ1c2VybmFtZSI6ImNhb2RhbzEyMzQzNCJ9LCJpYXQiOjE1NDQxODk5MjMsImV4cCI6MTU0NTA1MzkyM30.P4_BTd-ZuOtvQd0QlazlKigmDl9sVnvoKgjWjXmspdA";
allUser = getListData("select id from users");
allItem = getListData("select id from location");
data_from_database = pd.DataFrame(index=allUser,columns=allItem)
data_from_database[:] = -5;

allRating = getListObject("select id_user, id_location, score from evaluation")  
for i in allRating:
    if(i[0] in data_from_database.index and i[1] in data_from_database.columns):
        print(i[0]," - " ,i[1], " : ", i[2]);
        data_from_database.loc[i[0],i[1]] = i[2];


dictAverageScore = {};

for i in data_from_database.columns:
    listData = [item for item in data_from_database.loc[:,i] if item >= 0]
    if len(listData) == 0:
        dictAverageScore[i] = 0;
    else:
        dictAverageScore[i] = numpy.sum(listData) / len(listData);
        

recommend_data = recommendLocation(data_from_database, dictAverageScore) 
print(recommend_data)

app = Flask(__name__)
api = Api(app)

class RecommendTravel(Resource):
    def get(self, id_user):
        id_user = numpy.int64(id_user)
        passcodeFromClient = request.headers.get('passcode');
        if passcodeFromClient != passcode:
            return
        result = recommend_data.loc[id_user,:].tolist();
        print(recommend_data)
        print(result)
        return {"data" : [x for x in result if x != -1]  }
    
class AddNewLocation(Resource):
    def post(self):
        passcodeFromClient = request.headers.get('passcode')
        if passcodeFromClient != passcode:
            return
        id_location = request.form['id_location']
        id_location = numpy.int64(id_location)
        dictAverageScore[id_location] = 0;
        global data_from_database
        data_from_database.insert(loc=0, column=id_location, value=[-5] * len(data_from_database.index))
#         data_from_database = data_from_database.assign(id_location=[-5] * len(data_from_database.index))
#         data_from_database.rename(columns={'id_location': id_location}, inplace=True)
        print(data_from_database)
#         data_from_database.loc[:,id_location] = [-5] * len(data_from_database.index)
        return {"data" : "OK"}

class AddNewUser(Resource):
    def post(self):
        passcodeFromClient = request.headers.get('passcode')
        if passcodeFromClient != passcode:
            return
        id_user = request.form['id_user']
        id_user = numpy.int64(id_user)
        
        global data_from_database
#         columns_data = data_from_database.columns;
#         data_add = [-5] * len(columns_data);
        data_from_database = data_from_database.append(pd.Series([-5] * len(data_from_database.columns), index=data_from_database.columns, name=id_user))
        
        print("INDEX OF MAIN");
        print(data_from_database.index.tolist())
#         data_from_database = data_from_database.append(pd.DataFrame(data_add,index=id_user,columns=columns_data))
#         data_from_database.loc[id_user,:] = [-5] * len(data_from_database.columns);
#         recommend_data.loc[id_user,:] = data_from_database.columns.sort_values(ascending=False)[0:10]
        global recommend_data
        recommend_data = recommend_data.append(pd.Series(data_from_database.columns.sort_values(ascending=False)[0:10], index=recommend_data.columns, name=id_user))
        _thread.start_new_thread(recommendLocationForUser, (data_from_database, id_user, recommend_data, dictAverageScore) )
        return {"data" : "OK"}

class AddEvaluation(Resource):
    def post(self):
        passcodeFromClient = request.headers.get('passcode')
        if passcodeFromClient != passcode:
            return
        id_user = request.form['id_user']
        id_user = numpy.int64(id_user)
        id_location = request.form['id_location']
        id_location = numpy.int64(id_location)
        score = request.form['score']
        score = numpy.int64(score)
        
        listData = [item for item in data_from_database.loc[:,id_location].tolist() if item >= 0];
        if len(listData) == 0:
            dictAverageScore[id_location] = 0;
        else:
            dictAverageScore[id_location] = numpy.sum(listData) / len(listData);
        
        if data_from_database.loc[id_user,id_location] != score:
            data_from_database.loc[id_user,id_location] = score;
            _thread.start_new_thread(recommendLocationForUser, (data_from_database, id_user, recommend_data, dictAverageScore) )     
        return {"data" : "OK"}

class DeleteUser(Resource):
    def post(self):
        passcodeFromClient = request.headers.get('passcode')
        if passcodeFromClient != passcode:
            return
        id_user = request.form['id_user']
        id_user = numpy.int64(id_user)
        data_from_database.drop(id_user,inplace=True)
        recommend_data.drop(id_user,inplace=True)
        return {"data" : "OK"}
    
class DeleteLocation(Resource):
    def post(self):
        passcodeFromClient = request.headers.get('passcode')
        if passcodeFromClient != passcode:
            return
        id_location = request.form['id_location']
        id_location = numpy.int64(id_location)
        del dictAverageScore[id_location]
        del data_from_database[id_location]
        recommend_data.replace(id_location,-1,inplace=True)
        _thread.start_new_thread(reRecommendLocationForUser, (data_from_database, recommend_data, dictAverageScore ))
        return {"data" : "OK" } 
#     
api.add_resource(RecommendTravel, '/recommendTravel/<id_user>')
api.add_resource(AddNewLocation, '/addLocation')
api.add_resource(AddNewUser, '/addUser')
api.add_resource(AddEvaluation, '/addEvaluation')
api.add_resource(DeleteUser, '/deleteUser')
api.add_resource(DeleteLocation, '/deleteLocation')
    
if __name__ == '__main__':
    app.run(port='5002')
    