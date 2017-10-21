var postcss = require('gulp-postcss');
var gulp = require('gulp');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var htmlmin = require('gulp-htmlmin');
var babel = require('gulp-babel');
require('babel-preset-es2015');
gulp.task('js', () =>
          gulp.src(['./*.js', '!gulpfile.js'])
          .pipe(babel({
            presets: ['es2015']
          }))
          .pipe(gulp.dest('./public'))
         );

gulp.task('css', function () {
  var plugins = [
    autoprefixer({browsers: ['last 5 versions']}),
    cssnano()
  ];
  return gulp.src('./*.css')
    .pipe(postcss(plugins))
    .pipe(gulp.dest('./public'));
});

gulp.task('build', ['css', 'js']);
