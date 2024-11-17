class ElementSingleton:
    _dynamic_component = True

    def __init__(self, custom_id=None):
        self.e = elems
        self._name = self.__class__.__name__ if not custom_id else custom_id
        self._singleton = True
        self.e.register_elem(self)

    def update(self):
        pass
    
    def delete(self):
        self.e.delete_elem(self)

class Element:
    _dynamic_component = True

    def __init__(self, custom_id=None, singleton=False, register=False):
        self.register = register
        self.e = elems
        self._name = self.__class__.__name__ if not custom_id else custom_id
        self._singleton = singleton
        if self.register:
            self.e.register_elem(self)
    
    def update(self):
        pass
    
    def delete(self):
        self.e.delete_elem(self)

class Elements:
    def __init__(self):
        self.elems = {'duplicates': {}, 'singletons': {}}
        
    def delete_elem(self, elem):
        if not elem._singleton:
            if elem._name in self.elems['duplicates']:
                self.elems['duplicates'][elem._name].remove(elem)
    
    def register_elem(self, elem):
        if elem._singleton:
            if elem._name not in self.elems['singletons']:
                self.elems['singletons'][elem._name] = elem
        elif elem._name not in self.elems['duplicates']:
            self.elems['duplicates'][elem._name] = [elem]
        else:
            self.elems['duplicates'][elem._name].append(elem)
        
    # no error handling here to save on performance
    def __getitem__(self, key):
        return self.elems['singletons'][key]
    
    def group(self, key):
        if key in self.elems['duplicates']:
            return self.elems['duplicates'][key]
        return []

elems = Elements()