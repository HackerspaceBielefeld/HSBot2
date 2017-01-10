<?php
	error_reporting(E_ALL); 
	ini_set('error_reporting', E_ALL);
	echo '<html><head></head><body>
		<a href="index.php?a=infos">Infos</a> <a href="index.php?a=termin">Termine</a><hr/>';

	if(isset($_GET['a'])) {
		$a = $_GET['a'];
	}else{
		$a = '';
	}

	if($a == 'termin') {
		if(isset($_POST['submit'])) {
			$f = fopen('cache/schedule.csv',"w");
			$lines = array();
			foreach($_POST['name'] as $index => $name) {
				if($name != '') {
					$wd = date("w",mktime(12,0,0, $_POST['mon'][$index],$_POST['tag'][$index],$_POST['mon'][$index]));
					$lines[] = $name .';'. $_POST['zeit'][$index] .';'. $_POST['jahr'][$index] .';'. $_POST['mon'][$index] .';'. $_POST['tag'][$index] .';'. $wd; 
				}	
			}
			fputs($f,implode("\n",$lines));
			fclose($f);
			echo 'Daten angepasst<br/>';
		}

		$termine = file("cache/schedule.csv");
		echo '<table><form action="index.php?a=termin" method="post">
			<tr><td>Name</td><td>Zeit</td><td>Jahr</td><td>Monat</td><td>Tag</td></tr>';
		foreach($termine as $index => $termin) {
			$t = explode(';',$termin);
			echo '<tr>
				<td><input type="text" name="name['. $index .']" value="'. $t[0] .'" /></td>
				<td><input type="text" name="zeit['. $index .']" value="'. $t[1] .'" /></td>
				<td><input type="text" name="jahr['. $index .']" value="'. $t[2] .'" size="4" /></td>
				<td><input type="text" name="mon['. $index .']" value="'. $t[3] .'" size="4" /></td>
				<td><input type="text" name="tag['. $index .']" value="'. $t[4] .'" size="4" /></td>
			</tr>';
		}
		$index++;
		$now = explode('-',date("Y-m-d"));
		echo '<tr>
			<td><input type="text" name="name['. $index .']" value="" /></td>
			<td><input type="text" name="zeit['. $index .']" value="" /></td>
			<td><input type="text" name="jahr['. $index .']" value="'. $now[0] .'" size="4" /></td>
			<td><input type="text" name="mon['. $index .']" value="'. $now[1] .'" size="4" /></td>
			<td><input type="text" name="tag['. $index .']" value="'. $now[2] .'" size="4" /></td>
		</tr>
		<tr>
			<td colspan="5">
				<input type="submit" name="submit" value="Speichern" />
			</td>
		</tr>
		</form</table>';
	}
	
	if($a == 'infos') {
		if(isset($_GET['s'])) {
			if($_GET['s'] == 'del') {
				$f = str_replace('/','_',$_GET['f']);
				unlink('info/'.$f.'.txt');
				unset($_GET['f']);
			}
			
			if($_GET['s'] == 'act') {
				$f = str_replace('/','_',$_GET['f']);
				if(substr($f,0,1) == '.') {
					rename('info/'.$f.'.txt','info/'.substr($f,1) .'.txt');
				}else{
					rename('info/'.$f.'.txt','info/.'. $f .'.txt');
				}
				unset($_GET['f']);
			}
		}
		
		if(isset($_GET['f'])) {
			$f = str_replace('/','_',$_GET['f']);
			if(isset($_POST['submit'])) {
				$h = fopen('info/'.$f.'.txt','w');
				$content = str_replace("\r",'',$_POST['content']);
				flock($h,2);
				fputs($h, $content);
				flock($h,3);
				fclose($h);
			}else{
				$content = file('info/'.$f.'.txt');
				echo '<h2>'.$f.'</h2><form action="index.php?a=infos&f='. $f .'" method="post">
					<textarea name="content" cols="30" rows="10">'. implode('',$content) .'</textarea><br/>
					<input type="submit" name="submit" value="Editieren" />
				</form>';
			}
		}else{
			$d = opendir("info/");
			while($f = readdir($d)) {
				if(!is_dir("info/".$f)) {
					$f = substr($f,0,-4);
					echo '<a href="index.php?a=infos&f='. $f .'">'.$f.'</a> [<a href="index.php?a=infos&f='. $f .'&s=del">L&ouml;schen</a> <a href="index.php?a=infos&f='. $f .'&s=act">(De)Aktivieren</a>]<br/>';
				}
			}
			echo '<form action="index.php" method="get">
				<input type="hidden" name="a" value="infos" />
				<input type="text" name="f" /> <input type="submit" value="Anlegen" />
			</form';
		}
	}
?>
