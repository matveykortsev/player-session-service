import json

from flask import Flask, jsonify, request
from flask_caching import Cache
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.query import dict_factory
import datetime as dt

from model.sessions import SessionsSchema

BATCH = []

profile = ExecutionProfile(row_factory=dict_factory)

app = Flask(__name__)
app.config.from_object('config.BaseConfig')
cache = Cache(app)

cass = Cluster(['cassandra'], execution_profiles={EXEC_PROFILE_DEFAULT: profile})
cass_session = cass.connect()

player_query = cass_session.prepare("SELECT * FROM test.session_by_player_id WHERE player_id =? AND ts > '1970-01-01T00:00:00' LIMIT 1000")
country_query = cass_session.prepare("SELECT * FROM test.session_by_country WHERE country=? AND ts < ? AND ts > ?")
insert_query_country = cass_session.prepare("INSERT INTO test.session_by_country JSON ?")
insert_query_player_id = cass_session.prepare("INSERT INTO test.session_by_player_id JSON ?")


@app.route('/by-player/<player_id>', methods=['GET'])
@cache.cached(timeout=50, query_string=True)
def completed_sessions_by_player(player_id):
    sessions_obj = cass_session.execute(player_query, [player_id])
    schema = SessionsSchema(many=True)
    sessions = schema.dump(sessions_obj)
    complete_sessions = []
    for session in sessions:
        if len(complete_sessions) == 20:
            break
        if session['event'] == 'end':
            complete_sessions.append(session)
    return jsonify(complete_sessions)


@app.route('/by-country/<country>/<hours>', methods=['GET'])
@cache.cached(timeout=50, query_string=True)
def start_sessions_last_hours(country, hours):
    now_ts = dt.datetime.now()
    interval_ts = now_ts - dt.timedelta(hours=int(hours))
    sessions_obj = cass_session.execute(country_query, [country, now_ts, interval_ts])
    schema = SessionsSchema(many=True)
    sessions = schema.dump(sessions_obj)
    return jsonify(sessions)


@app.route('/event-handler', methods=["POST"])
def test_post():
    request_data = request.get_json()
    record = SessionsSchema().load(request_data)
    session = SessionsSchema().dump(record)
    if len(BATCH) < 10:
        BATCH.append(session)
    if len(BATCH) == 10:
        for piece in BATCH:
            if piece['event'] == 'start':
                json_piece = json.dumps(piece)
                cass_session.execute(insert_query_country, [json_piece])
                cass_session.execute(insert_query_player_id, [json_piece])
            if piece['event'] == 'end':
                json_piece = json.dumps(piece)
                cass_session.execute(insert_query_player_id, [json_piece])
        BATCH.clear()
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)