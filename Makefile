#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#  OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#

all:
	@echo "Targets: setup clean cleandata -- type 'make help' for a list of targets"

help:
	@echo "Targets:"
	@echo "	 make setup    -- Run the setup.py script as install "
	@echo "	 make pack     -- package PyEdPro "
	@echo "	 make remove   -- remove (all) traces of pyspass from the system."

setup:
	@python3 ./setup.py install

remove:
	@python3 ./setup.py install --record files.txt
	xargs rm -rf < files.txt
	@rm -f files.txt

pack:
	@./pack.sh

clean:
	rm -f *.pyc
	rm -rf __pycache__
	rm -rf build/*

cleandata:
	rm -f passdata.sqlt
	rm -f ~/.pyspass/passdata.sqlt
	rm -f ~/.pyspass/*.txt

git:
	git add .
	git commit -m autocheck
	git push

# End of Makefile
