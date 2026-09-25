# Custom column that uses MEDIUMTEXT for mysql databases
# This matters because the mysql TEXT column is very small,
# and VARCHAR won't fix it because it's limited by the table
# size limt, which is also small
#
# We choose MEDIUMTEXT over LONGTEXT because it's
# a) almost certainly good enough
# b) doesn't require fiddling with max_allowed_packet_size to
#    allow remote connections to work correctly with larger
#    entries


from sqlobject.col import SOUnicodeCol, Col


class SOCustomUnicodeCol(SOUnicodeCol):

    def _mysqlType(self):
        return 'MEDIUMTEXT'


class CustomUnicodeCol(Col):
    baseClass = SOCustomUnicodeCol
