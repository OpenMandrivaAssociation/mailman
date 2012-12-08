%define uid     mail
%define gid     mail
%define email_version   2.5.8

Name:       mailman
Version:    2.1.15
Release:    1
Summary:    The GNU Mailing List Management System
Group:      System/Servers
License:    GPL
URL:        http://www.list.org/
Source0:    http://ftp.gnu.org/gnu/mailman/%{name}-%{version}.tgz
Source1:    %{name}.init
Patch0:     %{name}-buildroot-check.patch
Patch1:     mailman-2.1.12-rename-arch.patch
Patch6:     %{name}-2.1.2-postfix-aliases.patch
Patch8:     %{name}-2.1.5-build.patch
Patch9:     %{name}-2.1.11-change-default-icons-url.patch
# http://non-gnu.uvt.nl/mailman-pgp-smime/
Patch100:	http://non-gnu.uvt.nl/pub/mailman/mailman-2.1.15-pgp-smime_2012-08-28.patch
Source100:	http://non-gnu.uvt.nl/pub/mailman/mailman-2.1.15-pgp-smime_2012-08-28.patch.md5
Requires:   mail-server
Requires:   apache
%py_requires -d
Requires:	python-GnuPG-Interface
Requires:	gnupg
Requires:	openssl
BuildRoot:          %{_tmppath}/%{name}-%{version}

%description
Mailman -- The GNU Mailing List Management System --
is a mailing list management system written mostly in
Python. Features:

  o Most standard mailing list features, including:
     moderation, mail based commands, digests, etc...
  o An extensive Web interface, customizable on a per-list basis.
  o Web based list administration interface for *all* admin-type tasks
  o Automatic Web based hypermail-style archives (using pipermail or
    other external archiver), including provisions for private archives
  o Integrated mail list to newsgroup gatewaying
  o Integrated newsgroup to mail list gatewaying (polling-based... if you
     have access to the nntp server, you should be able to easily do
     non-polling based news->mail list gatewaying; email viega@list.org,
     I'd like to help get that going and come up
     with instructions)
  o Smart bounce detection and correction
  o Integrated fast bulk mailing
  o Smart spam protection
  o Extensible logging
  o Multiple list owners and moderators are possible
  o Optional MIME-compliant digests
  o Nice about which machine you subscribed from if you're from the
        right domain

Conditional build options:
    mailman uid --with uid %{uid}
    mailman gid --with gid %{gid}

%prep
%setup -q
%patch0 -p1 -b .buildroot
%patch1 -p1 -b .rename-arch
%patch6 -p1 -b .chmod
%patch8
%patch9 -p1 -b .default
%patch100 -p1

%build
%serverbuild
# As a normal user, we don't have permissions to do this.  %patch0 changes
#   configure so that the directory check will never fail.
autoreconf
./configure \
    --prefix=%{_libdir}/%{name} \
    --with-var-prefix=%{_var}/lib/%{name} \
    --with-mail-gid=%{gid} \
    --with-cgi-gid=apache \
    --with-username=%{uid} \
    --with-groupname=%{gid} \
    --without-permcheck \
    --with-cgi-ext=.cgi \
    --libdir=%{_libdir}

make
# fix encoding typo
perl -pi -e 's/gb2132/gb2312/' misc/email-2.5.6/email/Charset.py

%install
rm -rf %{buildroot}
%makeinstall_std

# apache conf
install -d -m 755 %{buildroot}%{_webappconfdir}
cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# Mailman Apache configuration file
Alias /%{name}/icons %{_libdir}/%{name}/icons
Alias /%{name}       %{_libdir}/%{name}/cgi-bin
Alias /pipermail     %{_var}/lib/%{name}/archives/public


<Directory %{_libdir}/%{name}/cgi-bin>
    Order allow,deny
    Allow from all
    Options ExecCgi
    DirectoryIndex listinfo.cgi
</Directory>

<Directory %{_libdir}/%{name}/icons>
    Order allow,deny
    Allow from all
</Directory>

<Directory %{_var}/lib/mailman/archives/public>
    Order allow,deny
    Allow from all
    Options FollowSymlinks
</Directory>
EOF

# init script
install -d -m 755 %{buildroot}%{_initrddir}
install -m 755 misc/mailman %{buildroot}%{_initrddir}

# move logs directory into /var/log
install -d -m 755 %{buildroot}%{_var}/log
mv %{buildroot}%{_var}/lib/%{name}/logs %{buildroot}%{_var}/log/%{name}
(cd %{buildroot}%{_var}/lib/%{name} && ln -s ../../log/%{name} logs)

# move config file into /etc
install -d -m 755 %{buildroot}%{_sysconfdir}
mv %{buildroot}%{_libdir}/%{name}/Mailman/mm_cfg.py %{buildroot}%{_sysconfdir}/%{name}
(cd %{buildroot}%{_libdir}/%{name}/Mailman && ln -s ../../../..%{_sysconfdir}/%{name} mm_cfg.py)
rm -f %{buildroot}%{_libdir}/%{name}/Mailman/mm_cfg.py.dist

# fix permissions mess
chmod -R go=u-ws %{buildroot}%{_libdir}/%{name}
chmod 750 %{buildroot}%{_var}/lib/%{name}/archives/private

# logrotate
install -d m 755 %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/%{name} <<EOF
# daily rotated log files
%{_var}/log/mailman/smtp-failure %{_var}/log/mailman/smtp %{_var}/log/mailman/locks %{_var}/log/mailman/fromusenet %{_var}/log/mailman/qrunner {
    daily
    missingok
    rotate 7
    sharedscripts
    postrotate
    [ -f '/var/run/mailman/mailman.pid' ] && %{_libdir}/mailman/bin/mailmanctl -q reopen || exit 0
    endscript
}

# weekly rotated log files
%{_var}/log/mailman/bounce %{_var}/log/mailman/error %{_var}/log/mailman/vette %{_var}/log/mailman/mischief {
    weekly
    missingok
    rotate 4
    sharedscripts
    postrotate
    [ -f '/var/run/mailman/mailman.pid' ] && %{_libdir}/mailman/bin/mailmanctl -q reopen || exit 0
    endscript
}

# monthly rotated log files
%{_var}/log/mailman/digest %{_var}/log/mailman/subscribe %{_var}/log/mailman/post {
    monthly
    missingok
    rotate 12
    sharedscripts
    postrotate
    [ -f '/var/run/mailman/mailman.pid' ] && %{_libdir}/mailman/bin/mailmanctl -q reopen || exit 0
    endscript
}
EOF

# install init script
install -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}

# binaries symlinks from /usr/sbin
install -d -m 755 %{buildroot}%{_sbindir}
pushd %{buildroot}%{_sbindir}
for bin in ../..%{_libdir}/%{name}/bin/*; do
    ln -s $bin .
done
popd

cat > README.mdv <<EOF
Mandriva RPM specific notes

setup
-----
The setup used here differs from default one, to achieve better FHS compliance.
- the configuration file is /etc/mailman
- the log files are in /var/log/mailman
- the constant files are in /usr/lib/mailman
- the variable files are in /var/lib/mailman
Moreover, the perms used are most standard and secures. check_perms will
scream, but mailman runs fine.

post-installation
-----------------
Post-installation script attempts first to integrate mailman aliases file with
existing mail aliases. Then the server-wide 'mailman' list is automatically
created, with root@hostname as admin, and a randomly generated password. This
list is configured with generic default values, but its configuration should be
reviewed before usage.
The password is available in the notification message sent by mailman upon list
creation, and is also used as the site password. The mailman service has to be
started, and the SMTP server has to be running for the message to be correctly
delivered.

upgrade
-------
The alias db (/var/lib/mailman/data/aliases.db) should be owned by the same uid
and gid as the one used by mailman, mail.mail here. You may experience toubles
when upgrading from old releases of the packages.
EOF

%pre
if [ $1 = "2" ]; then
  if [ ! -L %{_libdir}/%{name}/Mailman/mm_cfg.py ]; then
    mv %{_libdir}/%{name}/Mailman/mm_cfg.py %{_sysconfdir}/%{name}.tmp
  fi
  if [ ! -L %{_var}/lib/%{name}/logs ]; then
    mv %{_var}/lib/%{name}/logs %{_var}/log/%{name}
  fi
fi

%post
%_post_service %{name}
%if %mdkversion < 201010
%_post_webapp
%endif

cd %{_libdir}/%{name}

if [ $1 = 1 ]; then
    # installation

    # generic tasks
    hostname=`hostname`
    domainname=`dnsdomainname`

    if [ -z "$domainname" ]; then
	domainname=localdomain
    fi

    # mailman basic configuration
    cat >>Mailman/mm_cfg.py <<EOF
DEFAULT_EMAIL_HOST = '$domainname'
DEFAULT_URL_HOST = '$hostname'
add_virtualhost(DEFAULT_URL_HOST, DEFAULT_EMAIL_HOST)
EOF

    # make sure mail user is allowed to use cron
    if [ -f %{_sysconfdir}/cron.allow ]; then
        if ! grep -q %{uid} %{_sysconfdir}/cron.allow; then
            echo "%{uid}" >> %{_sysconfdir}/cron.allow
        fi
    fi

    # add cron task
    crontab -u %{uid} %{_libdir}/%{name}/cron/crontab.in

    # add aliases
    %create_ghostfile %{_var}/lib/%{name}/data/aliases %{uid} %{gid} 660
    mta="`readlink /etc/alternatives/sendmail-command 2>/dev/null | cut -d . -f 2`"
    if [ "$mta" == "postfix" ]; then
        cat >>Mailman/mm_cfg.py <<EOF
MTA = 'Postfix'
EOF
        maps=`/usr/sbin/postconf -h alias_maps`
        postconf -e \
            "recipient_delimiter = +" \
            "unknown_local_recipient_reject_code = 550" \
            "alias_maps = $maps, hash:%{_var}/lib/%{name}/data/aliases"
        /usr/sbin/postalias %{_var}/lib/%{name}/data/aliases
    else
        cat >> %{_sysconfdir}/aliases <<EOF
:include:   %{_var}/lib/%{name}/data/aliases
EOF
        /usr/bin/newaliases
    fi

    # generate random password
    passwd=%_get_password 8

    # site password
    %{_sbindir}/mmsitepass $passwd > /dev/null

    if [ ! -f /var/lib/mailman/lists/mailman/config.pck ]; then
        # initial list creation and configuration
        su %{uid} \
            -c "%{_sbindir}/newlist mailman root@$hostname $passwd" > /dev/null
        su %{uid} \
            -c "%{_sbindir}/config_list -i /var/lib/mailman/data/sitelist.cfg mailman"
    fi

else
    # upgrade
    if [ -f %{_sysconfdir}/%{name}.tmp ]; then
        mv -f %{_sysconfdir}/%{name}.tmp %{_sysconfdir}/%{name}
    fi
fi

%preun
%_preun_service %{name}

%postun
%if %mdkversion < 201010
%_postun_webapp
%endif
if [ $1 = 0 ]; then
    # generic tasks

    # remove cron task
    crontab -u %{uid} -r

    # remove aliases
    mta="`readlink /etc/alternatives/sendmail-command 2>/dev/null | cut -d . -f 2`"
    if [ "$mta" == "postfix" ]; then
        database=`/usr/sbin/postconf -h alias_database | \
            sed -e 's|, hash:%{_var}/lib/%{name}/data/aliases||'`
        maps=`/usr/sbin/postconf -h alias_maps | \
            sed -e 's|, hash:%{_var}/lib/%{name}/data/aliases||'`
        postconf -e \
            "alias_database = $database" \
            "alias_maps = $maps"
    else
        sed -i -e '/:include:   %{_var}/lib/%{name}/data/aliases/d' \
            %{_sysconfdir}/aliases
    fi
    /usr/bin/newaliases
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc ACKNOWLEDGMENTS BUGS FAQ INSTALL NEWS* README* TODO* UPGRADING
%doc gnu-COPYING-GPL contrib/README.check_perms_grsecurity
%doc doc/*
# constant files
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/cron
%{_libdir}/%{name}/pythonlib
%{_libdir}/%{name}/scripts
%{_libdir}/%{name}/tests
%{_libdir}/%{name}/messages
%{_libdir}/%{name}/templates
%{_libdir}/%{name}/bin
%{_libdir}/%{name}/Mailman
%{_libdir}/%{name}/icons
%dir %{_libdir}/%{name}/mail
%attr(2755,root,%{gid}) %{_libdir}/%{name}/mail/*
%dir %{_libdir}/%{name}/cgi-bin
%attr(2755,root,%{gid}) %{_libdir}/%{name}/cgi-bin/*
# variable files
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}/data
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}/lists
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}/locks
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}/qfiles
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}/spam
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}/logs
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}/archives/public
%attr(-,%{uid},apache) %{_var}/lib/%{name}/archives/private
%attr(-,%{uid},%{gid}) %{_var}/log/%{name}
# configuration files
%{_initrddir}/%{name}
%config(noreplace) %{_webappconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/%{name}
%{_sbindir}/*


%changelog
* Wed May 04 2011 Oden Eriksson <oeriksson@mandriva.com> 2.1.13-7mdv2011.0
+ Revision: 666358
- mass rebuild

* Wed Feb 23 2011 Oden Eriksson <oeriksson@mandriva.com> 2.1.13-6
+ Revision: 639474
- sync with MDVSA-2011:036

* Sat Nov 06 2010 Funda Wang <fwang@mandriva.org> 2.1.13-5mdv2011.0
+ Revision: 593902
- rebuild for py2.7

* Sun Oct 03 2010 Oden Eriksson <oeriksson@mandriva.com> 2.1.13-4mdv2011.0
+ Revision: 582668
- roll back to the mailman-2.1.13-pgp-smime_2010-03-01.patch patch (#61180)
- fix one post error

* Fri Oct 01 2010 Oden Eriksson <oeriksson@mandriva.com> 2.1.13-3mdv2011.0
+ Revision: 582319
- sync with MDVSA-2010:191
- mailman-2.1.13-pgp-smime_2010-09-08

  + Guillaume Rousse <guillomovitch@mandriva.org>
    - fix log rotation (fix #59198)
    - drop smrsh support, let expert sendmails users manage it themselves

* Tue Mar 02 2010 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.13-1mdv2010.1
+ Revision: 513659
- keep group write permission on variable files, as cgi runs under apache uid and mail gid
- switch to 'open to all' default access policy
- use explicit .cgi extension, for a simpler apache configuration
- new version
- fix apache configuration file
- fix post/pre dependencies
- rely on filetrigger for reloading apache configuration begining with 2010.1, rpm-helper macros otherwise
- new version

* Mon Dec 21 2009 Oden Eriksson <oeriksson@mandriva.com> 2.1.12-6mdv2010.1
+ Revision: 480539
- bump release
- fixed a weird typo...

* Mon Dec 21 2009 Oden Eriksson <oeriksson@mandriva.com> 2.1.12-5mdv2010.1
+ Revision: 480537
- added pgp and s/mime support

* Fri Dec 04 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.12-4mdv2010.1
+ Revision: 473514
- better default apache configuration

* Sun Jul 19 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.12-3mdv2010.0
+ Revision: 397967
- keep cgi and icons under %%{_libdir}/%%{name}

* Thu Jul 16 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.12-2mdv2010.0
+ Revision: 396507
- ship more documentation
- files perms/owernship cleanup:
 - no setgid bit for constant dirs
 - no setgid bit for variables dirs, make them owned by mailman user
 - make private archive directory private (#51117)

* Sun Mar 29 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.12-1mdv2009.1
+ Revision: 362171
- new version, needed for python 2.6 compatibility (#49148)
- fix config file creation during post-installation
- rediff arch renaming patch

* Tue Feb 03 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.11-3mdv2009.1
+ Revision: 337131
- keep bash completion in its own package

* Thu Dec 25 2008 Funda Wang <fwang@mandriva.org> 2.1.11-2mdv2009.1
+ Revision: 318987
- rebuild for new python

* Sun Jul 06 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.11-1mdv2009.0
+ Revision: 232165
- new version
- drop charset patch, a substitution is easier
- drop CVE 2008-0564 patch, merged upstream
- sync init script with sympa one
- install all web stuff under /var/www/mailman

* Tue Jun 17 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.9-7mdv2009.0
+ Revision: 223586
- let's reintroduce virtualhost directive, with domain name as EMAIL_HOST now
  (even if incorrect, it will still be better than build-time default values set
  by configuration process)
- use MTA-specific alias file hashing procedure, as postfix alias_base isn't used anymore
- update postfix autoconfiguration with mailman documentation
- update postfix autoconfiguration to match current mailman documentation

* Tue Jun 17 2008 Thierry Vignaud <tv@mandriva.org> 2.1.9-6mdv2009.0
+ Revision: 223142
- rebuild

  + Guillaume Rousse <guillomovitch@mandriva.org>
    - apply defaul template to the mailman list
    - more detailed explanations about the notification message
    - various changes for post-installation:
    - don't add virtualhost directive to mailman configuration
    - don't add mailman alias file in postfix alias_database configuration
      Update README.mdv with a more explicit description of post-configuration
      process

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Fri Mar 07 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.9-4mdv2008.1
+ Revision: 181393
- fix CVE-2008-0564

* Wed Feb 27 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.9-3mdv2008.1
+ Revision: 175940
- rename arch executable to avoid confusion with coreutils arch binary (fix #38056)
- fix mailman linking from secure sendmail directory
- don't install README.mdv in %%_sbindir

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

* Mon Dec 17 2007 Thierry Vignaud <tv@mandriva.org> 2mdv2008.1-current
+ Revision: 129622
- kill re-definition of %%buildroot on Pixel's request
- s/Mandrake/Mandriva/


* Wed Mar 07 2007 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.9-2mdv2007.1
+ Revision: 134606
- use rpm-helper helper script for generating password
- import alias management procedure from sympa, so as to handle other MTAs as postfix
- use database directive also for postfix, to make newaliase command work
- don't set defaut language in configuration, as it breaks some settings without actual added value (fix #26834)

* Wed Dec 06 2006 Michael Scherer <misc@mandriva.org> 2.1.9-2mdv2007.1
+ Revision: 91527
- bump release ( forget to commit it )
- use --without-permcheck to allow package to build in iurt
- Import mailman

* Thu Sep 14 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.9-1mdv2007.0
- 2.1.9 final

* Wed Sep 13 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.9-0.rc1.2mdv2007.0
- drop cve-2005-3573 patch, 2.1.9 is not affected

* Sun Sep 10 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.9-0.rc1.1mdv2007.0
- new version, motivated by security fixes
- new webapp macro
- herein document for README.mdv
- unzip all patches
- new custom LSB-compliant initscript
- drop grsecurity patch and specific handling, we don't have secure kernel
  anymore
- don't attempt to create mailman list in %%post if a previous installation
  is found
- make listinfo default index page for web interface

* Wed Aug 23 2006 Olivier Thauvin <nanardon@mandriva.org> 2.1.8-2mdv2007.0
- fix initscript: restart didn't do a real start, mailmanctl sound like
  reload

* Fri May 05 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.8-1mdk
- New release 2.1.8
- rediff patch 9
- drop patch 11, merged upstream

* Thu Jan 19 2006 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.7-1mdk
- New release 2.1.7
- rediff patch11
- pitiful workaround for missing files (#17820)

* Mon Dec 05 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.6-8mdk
- security update for CVE-2005-3573 (P10), date-overflows (P11) (Stew Benedict <sbenedict@mandrakesoft.com>)

* Fri Nov 18 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.6-7mdk
- requires python (fix #19830)

* Wed Sep 07 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.6-6mdk
- revert to using symlinks for binaries, qrunner expect to find them in original location (fix #17983)
- requires rpm-helper for preinstall and preuninstall

* Thu Aug 25 2005 Michael Scherer <misc@mandriva.org> 2.1.6-5mdk
- rebuild to fix #17820

* Wed Aug 17 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.6-4mdk
- fix postinstall script

* Sun Aug 07 2005 Michael Scherer <misc@mandriva.org> 2.1.6-3mdk
- fix postinstall script

* Thu Jul 14 2005 Guillaume Rousse <guillomovitch@mandriva.org> 2.1.6-2mdk 
- new mail-server requires
- new apache rpm macros
- move binaries to /usr/sbin instead of symlinking them
- use %%serverbuild

* Thu Jun 23 2005 Oden Eriksson <oeriksson@mandriva.com> 2.1.6-1mdk
- 2.1.6
- added fixes for new apache
- use the %%mkrel macro
- rediffed P9
- drop the CAN-2004-1177 CAN-2005-0202 patches, it's implemented upstream
- don't nuke *.pyc files

* Wed Mar 02 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.1.5-15mdk
- fix #13651, MDKSA-2005:037 (CAN-2005-0202) (P101)
- nuke *.pyc files

* Fri Feb 18 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.1.5-14mdk
- spec file cleanups, remove the ADVX-build stuff
- strip away annoying ^M

* Thu Jan 27 2005 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-13mdk 
- condtional build options documented in package description
- spec cleanup

* Tue Jan 25 2005 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-12mdk 
- security update for CAN-2004-1177 (Stew Benedict <sbenedict@mandrakesoft.com>)

* Sat Jan 22 2005 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-11mdk 
- add binaries symlinks in /usr/sbin
- only change /etc/cron.allow if it already exists
- don't shipt duplicated icons
- herein document instead of external source whenever possible
- apache configuration file in /etc/httpd/webapps.d
- no more order for apache configuration
- spec cleanup
- don't change test scripts
- more complete README.mdk

* Tue Dec 07 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-10mdk 
- charset patch (David Relson <relson@osagesoftware.com>)

* Sat Dec 04 2004 Michael Scherer <misc@mandrake.org> 2.1.5-9mdk
- Rebuild for new python

* Mon Nov 15 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-8mdk 
- create and hash alias file at the same time as modificating postfix config, so as to prevent postfix crash at startup in full installation scenario (#10180)
- make smtpdaemon a prereq, as it is needed at post-installation
- silent post-installation
- no more python prereq
- spec cleanup

* Fri Sep 03 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-7mdk 
- dont specify perms and owner in logrotate configuration (David Relson <relson@osagesoftware.com>)

* Mon Aug 30 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-6mdk 
- use macros to make easier rebuilding with different uid & gid (David Relson <relson@osagesoftware.com>)

* Mon Aug 30 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-5mdk 
- fixed missing file in logrotate config

* Sun Jul 25 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-4mdk 
- patch build to avoid having buildroot in binaries, no more post-install compilation needed

* Fri Jul 23 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-3mdk 
- explicit libdir

* Fri Jul 02 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-2mdk 
- make sure mail user is allowed to use cron
- finer logrotate configuration (stolen from Debian)

* Wed Jun 02 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.5-1mdk
- new version

* Thu Apr 08 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.4-4mdk
- automatic setup at installation

* Thu Apr 01 2004 Guillaume Rousse <guillomovitch@mandrake.org> 2.1.4-3mdk
- added bash-completion

