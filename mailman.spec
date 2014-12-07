%define uid     mail
%define gid     mail
%define email_version   2.5.8

Summary:	The GNU Mailing List Management System
Name:		mailman
Version:	2.1.15
Release:	11
Group:		System/Servers
License:	GPLv2
Url:		http://www.list.org/
Source0:	http://ftp.gnu.org/gnu/mailman/%{name}-%{version}.tgz
Source1:	mailman-tmpfiles.conf
Source2:	mailman.service
Patch0:		%{name}-buildroot-check.patch
Patch1:		mailman-2.1.12-rename-arch.patch
Patch6:		%{name}-2.1.2-postfix-aliases.patch
Patch9:		%{name}-2.1.11-change-default-icons-url.patch
# http://non-gnu.uvt.nl/mailman-pgp-smime/
Patch100:	http://non-gnu.uvt.nl/pub/mailman/mailman-2.1.15-pgp-smime_2012-08-28.patch
Source100:	http://non-gnu.uvt.nl/pub/mailman/mailman-2.1.15-pgp-smime_2012-08-28.patch.md5
Requires:	mail-server
Requires:	apache
Requires:	apache-mod_socache_shmcb
Requires:	python-GnuPG-Interface
Requires:	gnupg
Requires:	openssl
BuildRequires:  python-devel

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
%apply_patches

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
%makeinstall_std

# apache conf
install -d -m 755 %{buildroot}%{_webappconfdir}
cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# Mailman Apache configuration file
Alias /%{name}/icons %{_libdir}/%{name}/icons
Alias /%{name}       %{_libdir}/%{name}/cgi-bin
Alias /pipermail     %{_var}/lib/%{name}/archives/public


<Directory %{_libdir}/%{name}/cgi-bin>
    Require all granted
    Options ExecCgi
    DirectoryIndex listinfo.cgi
</Directory>

<Directory %{_libdir}/%{name}/icons>
    Require all granted
</Directory>

<Directory %{_var}/lib/mailman/archives/public>
    Require all granted
    Options FollowSymlinks
</Directory>
EOF

install -p -D -m644 %{SOURCE1} %{buildroot}%{_sysconfdir}/tmpfiles.d/mailman.conf

mkdir -p %{buildroot}%{_docdir}/%{name}

# Systemd service file
mkdir -p %{buildroot}%{_unitdir}
install -m644 %{SOURCE2} %{buildroot}%{_unitdir}

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


# binaries symlinks from /usr/sbin
install -d -m 755 %{buildroot}%{_sbindir}
pushd %{buildroot}%{_sbindir}
for bin in ../..%{_libdir}/%{name}/bin/*; do
    ln -s $bin .
done
popd

cat > README.mdv <<EOF
RPM specific notes

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
%systemd_post mailman.service

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
:include:	%{_var}/lib/%{name}/data/aliases
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
%systemd_preun mailman.service
# rpm should not abort if last command run had non-zero exit status, exit cleanly
exit 0

%postun
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
        sed -i -e '/:include:	%{_var}/lib/%{name}/data/aliases/d' \
            %{_sysconfdir}/aliases
    fi
    /usr/bin/newaliases
fi

%systemd_postun_with_restart mailman.service

# rpm should not abort if last command run had non-zero exit status, exit cleanly
exit 0

%files
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
%{_unitdir}/mailman.service
%config(noreplace) %{_webappconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/tmpfiles.d/mailman.conf
%{_sbindir}/*

