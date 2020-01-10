$(document).ready(function () {
    //$(document.body).vide('img/video/ocean'); -- este script esta en el html del home
    var activo;
//animacion de logo al iniciar
    setTimeout(function () {
        $("body.home>div").addClass('activo');
        $("body.home #slider").addClass('activo');
        setTimeout(function () {
            setLogoPlace(true);
            activo = true;
        },3000);
    },3000);

//animacion de logo al click
    $("#logoimg").click(function () {
        activo = activo ? false : true;
        setLogoPlace(activo);
    });

//carrusel de textos en home
    $('.carousel').carousel({
        interval: 5000,
        ride: 'carousel',
        wrap: true
    });

    $('.slider').carousel({
        interval: 5000,
        ride: 'carousel',
        wrap: true
    });

//transicion entre vistas
    $('.gotolink').click(
        function(event){
            event.preventDefault();
            var url = $(this).attr('href');
            $("body.home>div").removeClass('activo');
            $("#logo").removeClass('active flip');
            $("#contenidohome").addClass('d-none');
            $("#loginform").removeClass('delay-1s fadeInDownBig');
            setTimeout(function () {
                $("#logo").addClass('zoomOut');
                $("#loginform").addClass('fadeOutUp');
                setTimeout(function () {
                    window.location = url;
                }, 500);
            }, 500);
        }
    );

//Tooltips
    $(function () {$('[data-toggle="tooltip"]').tooltip()});

//click cada item del menu
    $('.menu-item').click(
        function(event){
            event.preventDefault();
            var url = "http://demo12.solucionesofthard.com/web#menu_id=" + $(this).attr('menu') + "&action_id=" + $(this).attr('action');
            $("#menu").removeClass('zoomInLeft');
            $(".lineas").removeClass('delay-1s');
            $(".lineas").addClass('fadeOut');
            setTimeout(function () {
                $("#menu").addClass('zoomOutLeft');
                setTimeout(function () {
                    $("#logo").removeClass('active flip');
                    $("#logo").addClass('zoomOut');
                    $("#navigation").addClass('d-none');
                    //window.location = url;
                }, 500);
            }, 500);
            
        }
    );

//Animacion items menu
    $('.menu-item').hover(
        function(){
            var index = $(this).index();
            switch(index){
                case 0:
                    $('.l1').toggleClass('onhover-X x2');
                    $('.l2').toggleClass('onhoverX x1');
                    $('.lc').toggleClass('onhoverY y1');
                break;
                case 1:
                    $('.l1').toggleClass('onhoverX x2');
                    $('.l3').toggleClass('onhoverX x2');
                    $('.la').toggleClass('onhoverY y2');
                break;
                case 2:
                    $('.l2').toggleClass('onhover-X x1');
                    $('.l4').toggleClass('onhover-X x1');
                    $('.lf').toggleClass('onhoverY y3');
                break;
                case 3:
                    $('.l3').toggleClass('onhover-X x2');
                    $('.l4').toggleClass('onhoverX x1');
                    $('.l5').toggleClass('onhover-X x2');
                    $('.l6').toggleClass('onhoverX x1');
                    $('.lc').toggleClass('onhover-Y y1');
                    $('.ld').toggleClass('onhoverY y1');
                break;
                case 4:
                    $('.l5').toggleClass('onhoverX x2');
                    $('.l7').toggleClass('onhoverX x2');
                    $('.la').toggleClass('onhover-Y y2');
                    $('.lb').toggleClass('onhoverY y2');
                break;
                case 5:
                    $('.l6').toggleClass('onhover-X x1');
                    $('.l8').toggleClass('onhover-X x1');
                    $('.lf').toggleClass('onhover-Y y3');
                    $('.lg').toggleClass('onhoverY y3');
                break;
                case 6:
                    $('.l7').toggleClass('onhover-X x2');
                    $('.l8').toggleClass('onhoverX x1');
                    $('.l9').toggleClass('onhover-X x2');
                    $('.l10').toggleClass('onhoverX x1');
                    $('.ld').toggleClass('onhover-Y y1');
                    $('.le').toggleClass('onhoverY y1');
                break;
                case 7:
                    $('.l9').toggleClass('onhoverX x2');
                    $('.l11').toggleClass('onhoverX x2');
                    $('.lb').toggleClass('onhover-Y y2');
                break;
                case 8:
                    $('.l10').toggleClass('onhover-X x1');
                    $('.l12').toggleClass('onhover-X x1');
                    $('.lg').toggleClass('onhover-Y y3');
                break;
                case 9:
                    $('.l11').toggleClass('onhover-X x2');
                    $('.l12').toggleClass('onhoverX x1');
                    $('.le').toggleClass('onhover-Y y1');
                break;
            }
        }
    );
});

function setLogoPlace(val) {
    if (val) {
        $("#logo").addClass('active flip');
        $("#logo").removeClass('delay-1s flipInY');
        setTimeout(function () {
            $("#logo").children("p").addClass('active');
            $("#contenidohome").addClass('fadeInUp');
            $("#contenidohome").removeClass('d-none');
            $("#navigation").addClass('fadeIn');
            $("#navigation").removeClass('d-none');
        },3000);
    } else {
        $("#logo").removeClass('active flip');
        $("#logo").children("p").removeClass('active');
        $("#contenidohome").addClass('d-none');
        $("#contenidohome").removeClass('fadeInUp');
        $("#navigation").addClass('d-none');
        $("#navigation").removeClass('fadeIn');
    }
}