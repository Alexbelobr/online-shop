import os
import flaskr
import unittest
import tempfile


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
        flaskr.app.config['TESTING'] = True
        self.app = flaskr.app.test_client()
        flaskr.init_db(0)



    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flaskr.app.config['DATABASE'])

    def test_empty_db(self):
        rv = self.app.get('/')
        assert b'Unbelievable. No entries here so far' in rv.data

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('admin', 'admin')
        #перетворення "rv.data" в "str"
        assert 'You were logged in' in str(rv.data)
        rv = self.logout()
        #запис "str" в "data"
        assert b'You where logged out' in rv.data
        rv = self.login('adminx', 'admin')
        assert b'Invalid username' in rv.data
        rv = self.login('admin', 'adminx')
        assert b'Invalid password' in rv.data


#Нам необходимо также проверить как работает добавление сообщений.

    def test_massages(self):
        self.login('admin', 'admin')
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong>allowed here'
        ), follow_redirects=True)

        assert b'No entries here so far' not in rv.data
        assert b'&lt;Hello&gt;' in rv.data
        assert b'<strong>HTML</strong>allowed here' in rv.data






if __name__ == '__main__':
    unittest.main()
