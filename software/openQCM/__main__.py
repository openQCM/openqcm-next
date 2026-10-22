if __name__ == '__main__':
    # Imported inside the guard: spawned children re-run this module as
    # __mp_main__ and must not load the GUI (see run.py).
    from openQCM.app import OPENQCM
    OPENQCM().run()
