from app.models.user import User


def test_01_create_superuser(runner, db):
    email = 'superuser@fake.ru'
    password = 'password'
    result = runner.invoke(args=['create', 'superuser',
                                 '--email', email,
                                 '--password', password])
    assert result.exit_code == 0, \
        'Проверьте, что exit_code консольной команды 0'
    assert result.output == f'Superuser <{email}> created successfully\n', \
        'Проверьте, что после выполнения выводится сообщение'

    user = User.find_by_email(email)
    assert user.is_superuser is True, \
        'Проверьте, что у пользователя установлен флаг `is_superuser`'
