from application import myprofiles

def get_corpus_path():
    """コーパスのパスを取得
    内部引数からファイルに変更したので注意
    """
    # domain = os.getenv('USERDOMAIN', 'default')
    # pathdic = {
    #     'admin-PC': r'C:\Users\Rokuro Sato\Software\KNBC_v1.0_090925\KNBC_v1.0_090925',
    #     'NECROCK-PC': r'C:\Users\六郎\Ownbin\KNBC_v1.0_090925',
    #     'default': r'/home/rokurou/programs/KNBC_v1.0_090925'
    # }
    prof = myprofiles.Profile()
    if 'BCCWJ_DB_PATH' in prof.config:
        return prof.config['BCCWJ_DB_PATH']
    print('Error: there is no profile')
    raise FileNotFoundError()