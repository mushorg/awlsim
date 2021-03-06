#!/bin/sh

# basedir is the root of the test directory in the package
basedir="$(dirname "$0")"
[ "$(echo "$basedir" | cut -c1)" = '/' ] || basedir="$PWD/$basedir"

# rootdir is the root of the package
rootdir="$basedir/.."

die()
{
	echo "$*"
	exit 1
}

# $1=message
test_failed()
{
	echo "=== TEST FAILED ==="
	if [ $opt_softfail -eq 0 ]; then
		die "$@"
	else
		echo "$*"
		echo "^^^ TEST FAILED ^^^"
		[ $global_retval -eq 0 ] && global_retval=1
	fi
}

cleanup()
{
	[ -f "$test_time_file" ] && {
		rm -f "$test_time_file"
		test_time_file=
	}
}

cleanup_and_exit()
{
	cleanup
	exit 1
}

# $1=interpreter
# Returns version on stdout as:  MAJOR MINOR PATCHLEVEL
get_interpreter_version()
{
	local interpreter="$1"

	"$interpreter" -c 'import sys; print("%d %d %d" % sys.version_info[0:3]);' 2>/dev/null
}

# $1=interpreter $2=awl_file ($3ff additional options to awlsimcli)
run_awl_test()
{
	local interpreter="$1"
	local awl="$2"
	shift; shift

	# Check whether a project file with the same basename exists
	# If it exists, run that instead of the raw AWL file
	local dir="$(dirname "$awl")"
	local base="$(basename "$awl" .awl)"
	local awlpro="${dir}/${base}.awlpro"
	[ -r "$awlpro" ] && awl="$awlpro"

	command time -o "$test_time_file" -f '%E' \
	"$interpreter" "$rootdir/awlsimcli" --quiet --onecycle --extended-insns \
		--hardware debug:inputAddressBase=7:outputAddressBase=8:dummyParam=True \
		--cycle-time 60 \
		"$@" \
		"$awl" || {
			test_failed "Test '$(basename "$awl")' FAILED"
			return
	}
	echo "[OK: $(cat "$test_time_file")]"
}

# $1=interpreter $2=sh_file
run_sh_test()
{
	local interpreter="$1"
	local sh_file="$2"
	shift; shift

	[ -x "$sh_file" ] && die "SH-file '$sh_file' must NOT be executable"

	[ "$(echo "$sh_file" | cut -c1)" = '/' ] || local sh_file="./$sh_file"

	# Source the test file
	. "$basedir/sh-test.defaults"
	. "$sh_file"

	# Run the test
	( sh_test "$interpreter" )
	local result=$?

	[ $result -eq 0 ] || die "Test failed with error code $result"
	echo "[OK]"
}

# $1=interpreter $2=testfile(.awl/.sh) ($3ff additional options to awlsimcli or testfile)
run_test()
{
	local interpreter="$1"
	local testfile="$2"
	shift; shift

	# Don't run ourself
	[ "$(basename "$testfile")" = "run.sh" ] && return

	echo -n "Running test '$(basename "$testfile")' with '$(basename "$interpreter")' ... "

	# Check the file type and run the tester
	if [ "$(echo -n "$testfile" | tail -c4)" = ".awl" ]; then
		run_awl_test "$interpreter" "$testfile" "$@"
	elif [ "$(echo -n "$testfile" | tail -c3)" = ".sh" ]; then
		run_sh_test "$interpreter" "$testfile" "$@"
	else
		die "Test file type of '$testfile' not recognized"
	fi
}

# $1=interpreter, $2=directory
run_test_directory()
{
	local interpreter="$1"
	local directory="$2"

	echo "--- Entering directory '$directory'"
	# run .awl(pro) tests
	for entry in "$directory"/*; do
		[ -d "$entry" ] && continue
		[ "$(echo -n "$entry" | tail -c4)" = ".awl" ] || continue
		run_test "$interpreter" "$entry"
	done
	# run .sh tests
	for entry in "$directory"/*; do
		[ -d "$entry" ] && continue
		[ "$(echo -n "$entry" | tail -c3)" = ".sh" ] || continue
		run_test "$interpreter" "$entry"
	done
	# Recurse into subdirectories
	for entry in "$directory"/*; do
		[ -d "$entry" ] || continue
		run_test_directory "$interpreter" "$entry"
	done
	echo "--- Leaving directory '$directory'"
}

# $@=testfiles
do_tests()
{
	for interpreter in "$opt_interpreter" python2 python3 pypy pypy3 jython ipy; do
		[ -z "$interpreter" ] && continue
		which "$interpreter" >/dev/null 2>&1 || {
			echo "=== WARNING: '$interpreter' interpreter not found. Test skipped."
			echo
			[ -n "$opt_interpreter" ] && break || continue
		}

		local interp_ver="$(get_interpreter_version "$interpreter")"
		local interp_ver_dot="$(echo "$interp_ver" | tr ' ' '.')"
		local interp_major="$(echo "$interp_ver" | cut -d' ' -f 1)"
		local interp_minor="$(echo "$interp_ver" | cut -d' ' -f 2)"

		[ "$interp_major" -eq 2 -a "$interp_minor" -lt 7 ] && {
			echo "=== WARNING: '$interpreter' interpreter version '$interp_ver_dot' too old. Test skipped."
			echo
			[ -n "$opt_interpreter" ] && break || continue
		}

		echo "=== Running tests with '$interpreter' interpreter."
		if [ $# -eq 0 ]; then
			run_test_directory "$interpreter" "$basedir"
		else
			for opt in "$@"; do
				if [ -d "$opt" ]; then
					run_test_directory "$interpreter" "$opt"
				else
					run_test "$interpreter" "$opt"
				fi
			done
		fi
		echo

		[ -n "$opt_interpreter" ] && break
	done
}

show_help()
{
	echo "awlsim unit test script"
	echo
	echo "Usage: run.sh [OPTIONS] [testscript.awl/.sh]"
	echo
	echo "Options:"
	echo " -i|--interpreter INTER        Use INTER as interpreter for the tests"
	echo " -s|--softfail                 Do not abort on single test failures"
}

trap cleanup_and_exit INT TERM
trap cleanup EXIT
test_time_file="$(mktemp --tmpdir=/tmp awlsim-test-time.XXXXXX)"

opt_interpreter=
opt_softfail=0

while [ $# -ge 1 ]; do
	[ "$(echo "$1" | cut -c1)" != "-" ] && break

	case "$1" in
	-h|--help)
		show_help
		exit 0
		;;
	-i|--interpreter)
		shift
		opt_interpreter="$1"
		which "$opt_interpreter" >/dev/null 2>&1 ||\
			die "Interpreter '${opt_interpreter}' not found"
		;;
	-s|--softfail)
		opt_softfail=1
		;;
	*)
		echo "Unknown option: $1"
		exit 1
		;;
	esac
	shift
done

global_retval=0
do_tests "$@"

exit $global_retval
