from codecrumbs import attribute_renamed


class Test:
    "class with some renamings"

    cfg = attribute_renamed("config")

    def config():
        "The config attribute"
        return {"something": 5}

    attr = attribute_renamed("undocumented_attr")

    def undocumented_attr():
        return 42
