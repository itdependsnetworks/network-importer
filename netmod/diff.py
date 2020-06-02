

class Diff:
    """ """

    def __init__(self, obj_type: str, name: str):
        """

        Args:
          obj_type:
          name:

        Returns:

        """
        if not isinstance(obj_type, str):
            raise ValueError(f"obj_type must be a string (not {type(obj_type)})")

        if not isinstance(name, str):
            raise ValueError(f"name must be a string (not {type(name)})")

        self.type = obj_type
        self.name = name
        self.items = {}
        self.childs = {}
        self.missing_remote = None
        self.missing_local = None

    def __str__(self):
        """ """

        if self.missing_remote and self.missing_local:
            return f"{self.type}:{self.name} MISSING BOTH"
        if self.missing_remote:
            return f"{self.type}:{self.name} MISSING REMOTE"
        if self.missing_local:
            return f"{self.type}:{self.name} MISSING LOCAL"
        if not self.has_diffs():
            return f"{self.type}:{self.name} NO DIFF"

        return f"{self.type}:{self.name} {self.nbr_diffs()} DIFFs"

    def add_item(self, name: str, local, remote):
        """
        Add an item tin

        Args:
          name: name or unique identifier if the item
          local: value on the local system
          remote: value on the remote system

        Returns:

        """

        self.items[name] = DiffProp(name, local, remote)

    def add_child(self, child):
        """
        Attach a child object ( )
        The childs are organized by name,
        if a child with the same name already exist
        it will be overwritten

        Args:
          child: NetworkImporterDiff

        Returns:

        """
        self.childs[child.name] = child

    def nbr_diffs(self) -> int:
        """
        Return the number of items AKA diffs attached to the object

        Returns
            Int: number of items currently attached to the object
        """
        return len(self.items.keys())

    def has_diffs(self, include_childs: bool = True) -> bool:
        """
        return true if the object has some diffs,
        by default it recursively checks all childs as well

        Args:
          include_childs: Default value = True

        Returns:
            Bool
        """

        status = False

        if len(self.items.keys()) > 0:
            status = True

        if self.missing_remote or self.missing_local:
            status = True

        if not include_childs:
            return status

        for child in self.childs.values():
            if child.has_diffs():
                status = True

        return status

    def print_detailed(self, indent: int = 0):
        """

        Args:
          indent: Default value = 0

        Returns:

        """

        margin = " " * indent

        if self.missing_remote and self.missing_local:
            print(f"{margin}{self.type}: {self.name} MISSING BOTH")
        elif self.missing_remote:
            print(f"{margin}{self.type}: {self.name} MISSING REMOTE")
        elif self.missing_local:
            print(f"{margin}{self.type}: {self.name} MISSING LOCAL")
        else:
            print(f"{margin}{self.type}: {self.name}")
            for item in self.items.values():
                print(f"{margin}  {item.name}   L({item.local})   R({item.remote})")

        if len(self.childs) == 0:
            return True

        print(f"{margin}  Childs")
        for child in self.childs.values():
            if child.has_diffs():
                child.print_detailed(indent=indent + 4)

    def items_to_dict(self) -> dict:
        """
        Return a dictionnary of the local values for all the items attached to the object

        Returns:
            Dict: dictionnary of the local values for all the items attached to the object
        """

        items = {}
        for item in self.items.values():
            items[item.name] = item.local

        return items


class DiffProp:
    """
    Simple class to save together the local and the remote value of an object
    """

    def __init__(self, name: str, local, remote):
        """


        Args:
          name:
          local:
          remote:

        Returns:

        """

        self.name = name

        if (  # pylint: disable=unidiomatic-typecheck
            local is not None and remote is not None and type(local) != type(remote)
        ):
            raise ValueError(
                f"local and remote value must be of same type (local:{type(local)}, remote:{type(remote)})"
            )

        self.local = local
        self.remote = remote
