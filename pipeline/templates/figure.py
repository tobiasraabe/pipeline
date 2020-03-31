import matplotlib.pyplot as plt


{% include 'load_data.py' %}


def plot(df):
    fig, ax = plt.subplots()

    {% block plot %}{% endblock %}

    plt.savefig("{{ produces }}")


if __name__ == '__main__':
    df = load_data("{{ depends_on }}")
    plot(df)
