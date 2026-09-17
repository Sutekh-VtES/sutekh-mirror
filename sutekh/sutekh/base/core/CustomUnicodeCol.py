# Custom column that uses LONGTEXT for mysql databases
# This matters because the mysql TEXT column is very small,
# and VARCHAR won't fix it because it's limited by the table
# size limt, which is also small


from sqlobject.col import SOUnicodeCol, Col


class SOCustomUnicodeCol(SOUnicodeCol):

    def _mysqlType(self):
        return 'MEDIUMTEXT'


class CustomUnicodeCol(Col):
    baseClass = SOCustomUnicodeCol
