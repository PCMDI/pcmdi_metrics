#include <Python.h>
#include "numpy/arrayobject.h"

static PyObject * add(PyObject *self, PyObject *args) {
    PyObject *input,*input2;
    PyArrayObject *a1,*a2;
    int i;
    if (!PyArg_ParseTuple(args,"OO",&input,&input2))
        return NULL;

    a1 = (PyArrayObject *) PyArray_ContiguousFromObject(input,PyArray_NOTYPE,1,0);
    //bla bla


}

static PyMethodDef MyExtractMethods[]= {
    {"add", add, METH_VARARGS},
    {NULL, NULL} /* sentinel*/
};

void initexts() {
    (void) Py_InitModule("exts", MyExtractMethods);
    import_array()
  }

int main(int argc,char **argv)
  {
     Py_SetProgramName(argv[0]);
     Py_Initialize();
     initexts();
  }

