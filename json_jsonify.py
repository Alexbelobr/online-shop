from flask import json, jsonify,g

@app.route('/add_users')
def users_me():
    return jsonify(username=g.user.username)

    with user_set(app, my_user):
        with app.test_client() as c:
            resp = c.get('/add_users')
            data = json.loads(resp.data)
            self.assert_equal(data['username'], my_user.username)