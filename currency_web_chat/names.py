from faker import Faker


def get_full_name():
    fake = Faker()
    full_name = fake.name()
    return full_name


if __name__ == "__main__":
    name = get_full_name()
