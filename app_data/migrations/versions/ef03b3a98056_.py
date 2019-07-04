"""

Revision ID: ef03b3a98056
Revises: f32bd8265c3b
Create Date: 2019-07-05 12:53:17.236904

"""

# revision identifiers, used by Alembic.
revision = 'ef03b3a98056'
down_revision = 'f32bd8265c3b'

from odrs import db
from odrs.models import Component

def upgrade():

    # get all existing components
    components = {}
    for component in db.session.query(Component).\
                        filter(Component.app_id != '').\
                        order_by(Component.app_id.asc()).all():
        components[component.app_id] = component

    # guessed, thanks Canonical! :/
    for app_id in components:
        if not app_id.startswith('io.snapcraft.'):
            continue
        if components[app_id].component_id_parent:
            continue
        name, _ = app_id[13:].rsplit('-', maxsplit=1)
        parent = components.get(name + '.desktop')
        if not parent:
            continue
        print('adding snapcraft parent for {} -> {}'.format(components[app_id].app_id,
                                                            parent.app_id))
        parent.adopt(components[app_id])

    # from appstream-glib
    mapping = {
        'baobab.desktop': 'org.gnome.baobab.desktop',
        'bijiben.desktop': 'org.gnome.bijiben.desktop',
        'cheese.desktop': 'org.gnome.Cheese.desktop',
        'devhelp.desktop': 'org.gnome.Devhelp.desktop',
        'epiphany.desktop': 'org.gnome.Epiphany.desktop',
        'file-roller.desktop': 'org.gnome.FileRoller.desktop',
        'font-manager.desktop': 'org.gnome.FontManager.desktop',
        'gcalctool.desktop': 'gnome-calculator.desktop',
        'gcm-viewer.desktop': 'org.gnome.ColorProfileViewer.desktop',
        'geary.desktop': 'org.gnome.Geary.desktop',
        'gedit.desktop': 'org.gnome.gedit.desktop',
        'glchess.desktop': 'gnome-chess.desktop',
        'glines.desktop': 'five-or-more.desktop',
        'gnect.desktop': 'four-in-a-row.desktop',
        'gnibbles.desktop': 'gnome-nibbles.desktop',
        'gnobots2.desktop': 'gnome-robots.desktop',
        'gnome-2048.desktop': 'org.gnome.gnome-2048.desktop',
        'gnome-boxes.desktop': 'org.gnome.Boxes.desktop',
        'gnome-calculator.desktop': 'org.gnome.Calculator.desktop',
        'gnome-clocks.desktop': 'org.gnome.clocks.desktop',
        'gnome-contacts.desktop': 'org.gnome.Contacts.desktop',
        'gnome-dictionary.desktop': 'org.gnome.Dictionary.desktop',
        'gnome-disks.desktop': 'org.gnome.DiskUtility.desktop',
        'gnome-documents.desktop': 'org.gnome.Documents.desktop',
        'gnome-font-viewer.desktop': 'org.gnome.font-viewer.desktop',
        'gnome-maps.desktop': 'org.gnome.Maps.desktop',
        'gnome-nibbles.desktop': 'org.gnome.Nibbles.desktop',
        'gnome-photos.desktop': 'org.gnome.Photos.desktop',
        'gnome-power-statistics.desktop': 'org.gnome.PowerStats.desktop',
        'gnome-screenshot.desktop': 'org.gnome.Screenshot.desktop',
        'gnome-software.desktop': 'org.gnome.Software.desktop',
        'gnome-sound-recorder.desktop': 'org.gnome.SoundRecorder.desktop',
        'gnome-terminal.desktop': 'org.gnome.Terminal.desktop',
        'gnome-weather.desktop': 'org.gnome.Weather.Application.desktop',
        'gnomine.desktop': 'gnome-mines.desktop',
        'gnotravex.desktop': 'gnome-tetravex.desktop',
        'gnotski.desktop': 'gnome-klotski.desktop',
        'gtali.desktop': 'tali.desktop',
        'hitori.desktop': 'org.gnome.Hitori.desktop',
        'latexila.desktop': 'org.gnome.latexila.desktop',
        'lollypop.desktop': 'org.gnome.Lollypop.desktop',
        'nautilus.desktop': 'org.gnome.Nautilus.desktop',
        'polari.desktop': 'org.gnome.Polari.desktop',
        'sound-juicer.desktop': 'org.gnome.SoundJuicer.desktop',
        'totem.desktop': 'org.gnome.Totem.desktop',
        'akregator.desktop': 'org.kde.akregator.desktop',
        'apper.desktop': 'org.kde.apper.desktop',
        'ark.desktop': 'org.kde.ark.desktop',
        'blinken.desktop': 'org.kde.blinken.desktop',
        'cantor.desktop': 'org.kde.cantor.desktop',
        'digikam.desktop': 'org.kde.digikam.desktop',
        'dolphin.desktop': 'org.kde.dolphin.desktop',
        'dragonplayer.desktop': 'org.kde.dragonplayer.desktop',
        'filelight.desktop': 'org.kde.filelight.desktop',
        'gwenview.desktop': 'org.kde.gwenview.desktop',
        'juk.desktop': 'org.kde.juk.desktop',
        'kajongg.desktop': 'org.kde.kajongg.desktop',
        'kalgebra.desktop': 'org.kde.kalgebra.desktop',
        'kalzium.desktop': 'org.kde.kalzium.desktop',
        'kamoso.desktop': 'org.kde.kamoso.desktop',
        'kanagram.desktop': 'org.kde.kanagram.desktop',
        'kapman.desktop': 'org.kde.kapman.desktop',
        'kapptemplate.desktop': 'org.kde.kapptemplate.desktop',
        'kbruch.desktop': 'org.kde.kbruch.desktop',
        'kdevelop.desktop': 'org.kde.kdevelop.desktop',
        'kfind.desktop': 'org.kde.kfind.desktop',
        'kgeography.desktop': 'org.kde.kgeography.desktop',
        'kgpg.desktop': 'org.kde.kgpg.desktop',
        'khangman.desktop': 'org.kde.khangman.desktop',
        'kig.desktop': 'org.kde.kig.desktop',
        'kiriki.desktop': 'org.kde.kiriki.desktop',
        'kiten.desktop': 'org.kde.kiten.desktop',
        'klettres.desktop': 'org.kde.klettres.desktop',
        'klipper.desktop': 'org.kde.klipper.desktop',
        'KMail2.desktop': 'org.kde.kmail.desktop',
        'kmplot.desktop': 'org.kde.kmplot.desktop',
        'kollision.desktop': 'org.kde.kollision.desktop',
        'kolourpaint.desktop': 'org.kde.kolourpaint.desktop',
        'konsole.desktop': 'org.kde.konsole.desktop',
        'Kontact.desktop': 'org.kde.kontact.desktop',
        'korganizer.desktop': 'org.kde.korganizer.desktop',
        'krita.desktop': 'org.kde.krita.desktop',
        'kshisen.desktop': 'org.kde.kshisen.desktop',
        'kstars.desktop': 'org.kde.kstars.desktop',
        'ksudoku.desktop': 'org.kde.ksudoku.desktop',
        'ktouch.desktop': 'org.kde.ktouch.desktop',
        'ktp-log-viewer.desktop': 'org.kde.ktplogviewer.desktop',
        'kturtle.desktop': 'org.kde.kturtle.desktop',
        'kwordquiz.desktop': 'org.kde.kwordquiz.desktop',
        'marble.desktop': 'org.kde.marble.desktop',
        'okteta.desktop': 'org.kde.okteta.desktop',
        'parley.desktop': 'org.kde.parley.desktop',
        'partitionmanager.desktop': 'org.kde.PartitionManager.desktop',
        'picmi.desktop': 'org.kde.picmi.desktop',
        'rocs.desktop': 'org.kde.rocs.desktop',
        'showfoto.desktop': 'org.kde.showfoto.desktop',
        'skrooge.desktop': 'org.kde.skrooge.desktop',
        'step.desktop': 'org.kde.step.desktop',
        'yakuake.desktop': 'org.kde.yakuake.desktop',
        'colorhug-ccmx.desktop': 'com.hughski.ColorHug.CcmxLoader.desktop',
        'colorhug-flash.desktop': 'com.hughski.ColorHug.FlashLoader.desktop',
        'dconf-editor.desktop': 'ca.desrt.dconf-editor.desktop',
        'feedreader.desktop': 'org.gnome.FeedReader.desktop',
        'qtcreator.desktop': 'org.qt-project.qtcreator.desktop',
    }
    for app_id in mapping:
        if not app_id in components:
            continue
        app_id_new = mapping[app_id]
        if not app_id_new in components:
            continue
        if components[app_id].component_id_parent:
            continue
        print('adding legacy parent for {} -> {}'.format(components[app_id].app_id,
                                                         components[app_id_new].app_id))
        components[app_id_new].adopt(components[app_id])

    # upstream drops the .desktop sometimes
    for app_id in components:
        if components[app_id].component_id_parent:
            continue
        app_id_new = app_id.replace('.desktop', '')
        if app_id == app_id_new:
            continue
        if not app_id_new in components:
            continue
        print('adding parent for {} -> {}'.format(components[app_id].app_id,
                                                  components[app_id_new].app_id))
        components[app_id_new].adopt(components[app_id])

    # done
    db.session.commit()

def downgrade():
    pass
