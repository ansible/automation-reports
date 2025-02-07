import tempfile
import os

SUBID_MIN = 100000


def run(module, result):
    module_name = module._name.split(".")[-1]
    if module_name == "subuid":
        name = module.params["user"]
    elif module_name == "subgid":
        name = module.params["group"]
    else:
        module.fail_json(msg="unimplemented", **result)

    data = []
    found_at_index = None  # index is line number -1

    subid_file = "/etc/{}".format(module_name)
    if os.path.exists(subid_file):
        with open(subid_file) as f:
            index = 0
            for line in f:
                if not line.strip() or line.strip().startswith("#"):
                    continue

                [_name, range_start, range_size] = line.strip().split(":")

                data.append(
                    {
                        "name": _name,
                        "range_start": int(range_start),
                        "range_size": int(range_size),
                    }
                )

                if _name == name:
                    found_at_index = index

                index += 1

    state = module.params["state"]

    allowed_states = {"present", "absent"}

    if state not in allowed_states:
        module.fail_json(msg="state must be one of: present, allowed", **result)

    start = module.params["start"]
    count = module.params["count"]

    if state == "absent":
        if found_at_index is not None:
            del data[found_at_index]

            result["changed"] = True

    if state == "present":
        if found_at_index is not None:
            if start and data[found_at_index]["range_start"] != start:
                data[found_at_index]["range_start"] = start
                result["changed"] = True

            if data[found_at_index]["range_size"] != count:
                data[found_at_index]["range_size"] = count
                result["changed"] = True
        else:
            if start is None:
                if data:
                    # find next available id
                    all_uids = [line["range_start"] for line in data]
                    highest_uid = max(all_uids)
                    size_of_highest_range = data[all_uids.index(highest_uid)][
                        "range_size"
                    ]
                    start = highest_uid + size_of_highest_range
                else:
                    # file doesn't exist or empty
                    start = SUBID_MIN

            data.append(
                {
                    "name": name,
                    "range_start": start,
                    "range_size": count,
                }
            )
            result["changed"] = True

    if result["changed"]:
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        os.chmod(tmpfile.name, 0o644)

        for line in data:
            line = [line["name"], line["range_start"], line["range_size"]]
            tmpfile.write("{}:{}:{}\n".format(*line).encode())

        tmpfile.close()

        module.atomic_move(tmpfile.name, subid_file)
