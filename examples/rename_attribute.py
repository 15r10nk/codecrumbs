from codecrumbs import renamed_attribute


class Test:
    "class with some renamings"

    cfg = renamed_attribute("config")

    def config():
        "The config attribute"
        return {"something": 5}

    attr = renamed_attribute("undocumented_attr")

    def undocumented_attr():
        return 42
