# pyspass

## Password manager

Under construction. DO NOT USE.

## Password generator / manager

A python / PyGObject version of the popular password manager concept.

 Generates passes from Site / Login / Serial / Master Pass

SHA256 strong. No passes are saved, only site, site login name and
serial number is saved.

 The hashes are calculated at the time of master pass entry, and compared
to the checksum field. This assures that there are no sensitive items stored.

 The only item that cannot be calculated is the pass override. (custom pass)
that is stored with AES encryption.

 Pass is displayed as a QR code. (For your eyes only)
The default tab is for the site, the pass QR is not shown unless 'Auth' is
selected, and the master pass is successfully entered.

## Safety

  The SHA256 hash algorythm is considered unbreakable, and the AES encryption
is also unbreakable as in 2024. Because only the hshes are stored, no
compromizable items are saved.

![Screen Shot](screen3.png)

 We selected 16 letter long pass as default. Below a table of
  difficulty for breaking

![Screen Shot](passtable.png)

// EOF
